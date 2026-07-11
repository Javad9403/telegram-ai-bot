import logging
import httpx

logger = logging.getLogger(__name__)


class PhotoSearchClient:
    def __init__(self, api_key: str, base_url: str = "https://api.unsplash.com"):
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, per_page: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Unsplash API key not configured")
            return []

        headers = {"Authorization": f"Client-ID {self.api_key}"}
        params = {"query": query, "per_page": per_page, "orientation": "landscape"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/search/photos", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for photo in data.get("results", []):
                    results.append({
                        "url": photo.get("urls", {}).get("regular"),
                        "thumb": photo.get("urls", {}).get("thumb"),
                        "description": photo.get("description") or photo.get("alt_description") or "Photo",
                        "photographer": photo.get("user", {}).get("name"),
                        "photographer_url": photo.get("user", {}).get("links", {}).get("html"),
                        "url": photo.get("links", {}).get("html"),
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


class PexelsPhotoClient:
    def __init__(self, api_key: str, base_url: str = "https://api.pexels.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    async def search(self, query: str, per_page: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("Pexels API key not configured")
            return []

        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": per_page, "orientation": "landscape"}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/search", headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for photo in data.get("photos", []):
                    results.append({
                        "url": photo.get("src", {}).get("large"),
                        "thumb": photo.get("src", {}).get("medium"),
                        "description": photo.get("alt", "Photo"),
                        "photographer": photo.get("photographer"),
                        "photographer_url": photo.get("photographer_url"),
                        "url": photo.get("url"),
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