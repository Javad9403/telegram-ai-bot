import logging
import httpx

logger = logging.getLogger(__name__)


class UnsplashClient:
    def __init__(self, access_key: str, base_url: str = "https://api.unsplash.com"):
        self.access_key = access_key
        self.base_url = base_url

    async def search(self, query: str, per_page: int = 10) -> list[dict]:
        if not self.access_key:
            logger.warning("Unsplash access key not configured")
            return []

        headers = {"Authorization": f"Client-ID {self.access_key}"}
        params = {"query": query, "per_page": min(per_page, 30), "orientation": "landscape"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/search/photos", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for photo in data.get("results", []):
                    results.append({
                        "url": photo.get("urls", {}).get("regular"),
                        "thumb": photo.get("urls", {}).get("thumb"),
                        "description": photo.get("description") or photo.get("alt_description") or "Photo",
                        "photographer": photo.get("user", {}).get("name", "Unknown"),
                        "photographer_url": photo.get("user", {}).get("links", {}).get("html", ""),
                        "url": photo.get("links", {}).get("html", ""),
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during photo search: {e}")
            return []