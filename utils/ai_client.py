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
            logger.error("AI API call failed: %s", e)
            yield "Sorry, I'm having trouble connecting to the AI. Please try again later."
