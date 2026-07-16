import logging

from config import config
from tavily import AsyncTavilyClient

logger = logging.getLogger(__name__)


class TavilyClient:
    def __init__(self, api_key: str | None = None, proxy_url: str | None = None):
        self.api_key = api_key or config.tavily_api_key
        self.client = AsyncTavilyClient(api_key=self.api_key)

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            return [{"title": "Search unavailable", "snippet": "Tavily API key not configured. Please add TAVILY_API_KEY to .env", "link": ""}]

        try:
            response = await self.client.search(
                query=query,
                max_results=num_results,
                search_depth="basic",
                include_answer=False,
                include_raw_content=False,
            )

            results = []
            for result in response.get("results", [])[:num_results]:
                results.append({
                    "title": result.get("title", "No title"),
                    "snippet": result.get("content", "No description available"),
                    "link": result.get("url", ""),
                })

            return results

        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return [{"title": "Search error", "snippet": f"Search failed: {e}", "link": ""}]

    async def close(self):
        pass


def get_search_client():
    return TavilyClient()