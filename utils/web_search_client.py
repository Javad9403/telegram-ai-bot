import logging

import httpx

from config import config

logger = logging.getLogger(__name__)


class TavilyClient:
    def __init__(self, api_key: str | None = None, proxy_url: str | None = None):
        self.api_key = api_key or config.tavily_api_key
        self.proxy_url = proxy_url or config.proxy_url_resolved
        self.base_url = "https://api.tavily.com"
        self.client = httpx.AsyncClient(
            proxy=self.proxy_url,
            timeout=httpx.Timeout(30.0),
            headers={"Content-Type": "application/json"},
        )

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            return [{"title": "Search unavailable", "snippet": "Tavily API key not configured. Please add TAVILY_API_KEY to .env", "link": ""}]

        try:
            response = await self.client.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for result in data.get("results", [])[:num_results]:
                results.append({
                    "title": result.get("title", "No title"),
                    "snippet": result.get("content", "No description available"),
                    "link": result.get("url", ""),
                })

            return results

        except httpx.RequestError as e:
            logger.error(f"Tavily request failed: {e}")
            return [{"title": "Search error", "snippet": f"Failed to search: {e}", "link": ""}]
        except httpx.HTTPStatusError as e:
            logger.error(f"Tavily HTTP error: {e}")
            return [{"title": "Search error", "snippet": f"Search returned error: {e.response.status_code}", "link": ""}]
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return [{"title": "Search error", "snippet": f"Search failed: {e}", "link": ""}]

    async def close(self):
        await self.client.aclose()


def get_search_client():
    return TavilyClient()