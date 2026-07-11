import logging
import httpx

logger = logging.getLogger(__name__)


class DeezerSearchClient:
    def __init__(self, base_url: str = "https://api.deezer.com"):
        self.base_url = base_url

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        params = {"q": query, "limit": limit}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("data", []):
                    results.append({
                        "title": item.get("title", "Unknown Title"),
                        "artist": item.get("artist", {}).get("name", "Unknown Artist"),
                        "album": item.get("album", {}).get("title", "Unknown Album"),
                        "duration": item.get("duration", 0),
                        "preview_url": item.get("preview"),
                        "cover_url": item.get("album", {}).get("cover_big") or item.get("album", {}).get("cover_medium"),
                        "link": item.get("link"),
                        "source": "Deezer",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during Deezer search: {e}")
            return []


class YouTubeMusicSearchClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if not self.api_key:
            logger.warning("YouTube API key not configured")
            return []

        params = {
            "part": "snippet",
            "q": f"{query} music",
            "type": "video",
            "videoCategoryId": "10",
            "maxResults": limit,
            "key": self.api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/search", params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for item in data.get("items", []):
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    results.append({
                        "title": snippet["title"],
                        "artist": snippet["channelTitle"],
                        "album": "",
                        "duration": 0,
                        "preview_url": "",
                        "cover_url": snippet["thumbnails"]["high"]["url"],
                        "link": f"https://www.youtube.com/watch?v={video_id}",
                        "source": "YouTube Music",
                        "video_id": video_id,
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during YouTube music search: {e}")
            return []


class SoundCloudSearchClient:
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.base_url = "https://api-v2.soundcloud.com"

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if not self.client_id:
            logger.warning("SoundCloud client ID not configured")
            return []

        params = {"q": query, "limit": limit, "client_id": self.client_id}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{self.base_url}/search/tracks", params=params)
                response.raise_for_status()
                data = response.json()
                results = []
                for track in data.get("collection", []):
                    duration_ms = track.get("duration", 0)
                    minutes = duration_ms // 60000
                    seconds = (duration_ms % 60000) // 1000
                    results.append({
                        "title": track.get("title", "Unknown"),
                        "artist": track.get("user", {}).get("username", "Unknown"),
                        "album": "",
                        "duration": minutes * 60 + seconds,
                        "preview_url": track.get("stream_url"),
                        "cover_url": track.get("artwork_url"),
                        "link": track.get("permalink_url"),
                        "source": "SoundCloud",
                    })
                return results
        except httpx.RequestError as e:
            logger.error(f"HTTP request failed: {e}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP status error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred during SoundCloud search: {e}")
            return []