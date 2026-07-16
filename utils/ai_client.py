import logging
import json
import base64

import httpx
from openai import AsyncOpenAI

from utils.web_search_client import get_search_client

logger = logging.getLogger(__name__)

WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information, news, facts, or answers to questions that require up-to-date knowledge. Use this when the user asks about recent events, current prices, weather, news, technical documentation, or any topic requiring live information. Set deep=true if user wants comprehensive results or explicitly asks for more sources.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to use. Be specific and include relevant keywords.",
                },
                "deep": {
                    "type": "boolean",
                    "description": "Set to true if user wants comprehensive results or explicitly asks for more sources/details. Default is false (returns 2 concise results).",
                    "default": False,
                },
            },
            "required": ["query"],
        },
    },
}


class AIClient:
    def __init__(self, base_url: str, api_key: str, model: str, vision_base_url: str = "", vision_api_key: str = "", vision_model: str = ""):
        http_client = httpx.AsyncClient(trust_env=False)
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
        self.model = model
        
        self.vision_client = None
        if vision_base_url and vision_api_key and vision_model:
            vision_http_client = httpx.AsyncClient(trust_env=False)
            self.vision_client = AsyncOpenAI(base_url=vision_base_url, api_key=vision_api_key, http_client=vision_http_client)
            self.vision_model = vision_model
        else:
            self.vision_model = model
            self.vision_client = self.client

    async def get_response(self, messages: list[dict], stream: bool = True) -> str:
        # Check if any message contains images (vision request)
        use_vision = False
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "image_url":
                        use_vision = True
                        break
            if use_vision:
                break

        client = self.vision_client if use_vision else self.client
        model = self.vision_model if use_vision else self.model

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                tools=[WEB_SEARCH_TOOL] if not use_vision else None,
                tool_choice="auto" if not use_vision else None,
            )

            if stream:
                full_content = ""
                tool_calls = []
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta:
                        if delta.content:
                            full_content += delta.content
                            yield full_content
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                if len(tool_calls) <= tc.index:
                                    tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                                tool_calls[tc.index]["id"] = tc.id or tool_calls[tc.index]["id"]
                                if tc.function.name:
                                    tool_calls[tc.index]["function"]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

                if tool_calls:
                    async for chunk in self._handle_tool_calls(messages, full_content, tool_calls, stream):
                        yield chunk
            else:
                content = response.choices[0].message.content or ""
                tool_calls = response.choices[0].message.tool_calls or []
                if tool_calls:
                    tool_calls = [
                        {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                        for tc in tool_calls
                    ]
                    async for chunk in self._handle_tool_calls(messages, content, tool_calls, stream):
                        yield chunk
                else:
                    yield content

        except Exception as e:
            error_msg = str(e).lower()
            logger.error("AI API call failed: %s", e)
            if "insufficient_quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                yield "I've run out of API tokens. Please ask the admin to top up the account."
            elif "invalid_api_key" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
                yield "The API key is invalid. Please check the configuration."
            elif "model_not_found" in error_msg or "not found" in error_msg:
                yield f"The AI model '{self.model}' was not found. Try a different model."
            else:
                yield "Sorry, I'm having trouble connecting to the AI. Please try again later."

    async def analyze_image(self, image_data: bytes, prompt: str = "Describe this image in detail.", stream: bool = True) -> str:
        if not self.vision_client or not self.vision_model:
            yield "Vision model is not configured. Please configure VISION_MODEL, VISION_BASE_URL, and VISION_API_KEY."
            return

        try:
            base64_image = base64.b64encode(image_data).decode("utf-8")
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]

            response = await self.vision_client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                stream=stream,
                max_tokens=1024,
            )

            if stream:
                full_content = ""
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        full_content += delta.content
                        yield full_content
            else:
                yield response.choices[0].message.content or ""

        except Exception as e:
            error_msg = str(e).lower()
            logger.error("Vision API call failed: %s", e)
            if "insufficient_quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                yield "Vision API quota exceeded. Please ask the admin to top up the account."
            elif "invalid_api_key" in error_msg or "401" in error_msg or "unauthorized" in error_msg:
                yield "The Vision API key is invalid. Please check the configuration."
            elif "model_not_found" in error_msg or "not found" in error_msg:
                yield f"The vision model '{self.vision_model}' was not found. Try a different model."
            else:
                yield "Sorry, I'm having trouble analyzing the image. Please try again later."

    async def _handle_tool_calls(self, messages: list[dict], content: str, tool_calls: list, stream: bool):
        search_client = get_search_client()
        messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})

        for tool_call in tool_calls:
            if tool_call["function"]["name"] == "web_search":
                try:
                    args = json.loads(tool_call["function"]["arguments"])
                    query = args.get("query", "")
                    deep = args.get("deep", False)
                    if query:
                        logger.info(f"AI requested web search: {query} (deep={deep})")
                        results = await search_client.search(query, deep=deep)
                        results_text = self._format_search_results(results)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": results_text,
                        })
                except Exception as e:
                    logger.error(f"Web search tool error: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": f"Search failed: {e}",
                    })

        search_client = None

        try:
            follow_up = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
            )

            if stream:
                full_content = ""
                async for chunk in follow_up:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        full_content += delta.content
                        yield full_content
            else:
                yield follow_up.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Follow-up AI call failed: {e}")
            yield "I found some information but had trouble formulating a response."

    def _format_search_results(self, results: list[dict]) -> str:
        if not results:
            return "No search results found."

        formatted = "Web search results:\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No description")
            link = result.get("link", "")
            formatted += f"{i}. {title}\n{snippet}\n"
            if link:
                formatted += f"Source: {link}\n"
            formatted += "\n"
        return formatted
