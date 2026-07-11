import logging
import httpx

logger = logging.getLogger(__name__)


class SerperSearchClient:
    def __init__(self, api_key: str, base_url: str = "https://google.serper.dev/search"):
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Serper API key not configured")
            return []

        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": min(num_results, 10)}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("organic", []):
                    results.append({
                        "title": item.get("title", "No title"),
                        "snippet": item.get("snippet", "No description"),
                        "link": item.get("link", ""),
                        "source": "Google (Serper)",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Serper search: {e}")
            return []


class GoogleSearchClient:
    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        if not self.api_key or not self.cx:
            logger.warning("Google API key or CX not configured")
            return []

        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(num_results, 10),
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("items", []):
                    results.append({
                        "title": item.get("title", "No title"),
                        "snippet": item.get("snippet", "No description"),
                        "url": item.get("link", ""),
                        "source": "Google",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Google search: {e}")
            return []


class BingSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"

    async def search(self, query: str, count: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Bing API key not configured")
            return []

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {"q": query, "count": count, "responseFilter": "Webpages"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("webPages", {}).get("value", []):
                    results.append({
                        "title": item.get("name", "No title"),
                        "snippet": item.get("snippet", "No description"),
                        "url": item.get("url", ""),
                        "source": "Bing",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Bing search: {e}")
            return []


class DuckDuckGoClient:
    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                results = []

                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", "Result"),
                        "snippet": data.get("Abstract", ""),
                        "url": data.get("AbstractURL", ""),
                        "source": "DuckDuckGo",
                    })

                for topic in data.get("RelatedTopics", [])[:max_results - 1]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Text", "").split(" - ")[0],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "DuckDuckGo",
                        })

                return results[:max_results]
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during DuckDuckGo search: {e}")
            return []


class BraveSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(self, query: str, count: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Brave Search API key not configured")
            return []

        headers = {"Accept": "application/json", "X-Subscription-Token": self.api_key}
        params = {"q": query, "count": count}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("web", {}).get("results", []):
                    results.append({
                        "title": item.get("title", "No title"),
                        "snippet": item.get("description", "No description"),
                        "url": item.get("url", ""),
                        "source": "Brave",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Brave search: {e}")
            return []