import logging

import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class AIClient:
    def __init__(self, base_url: str, api_key: str, model: str):
        http_client = httpx.AsyncClient(trust_env=False)
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
        self.model = model

    async def get_response(self, messages: list[dict], stream: bool = True) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
            )

            if stream:
                full_content = ""
                async for chunk in response:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        full_content += delta.content
                        yield full_content
            else:
                content = response.choices[0].message.content or ""
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
