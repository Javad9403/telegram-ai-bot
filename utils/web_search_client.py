import logging
import re

import httpx

from config import config

logger = logging.getLogger(__name__)


class DuckDuckGoClient:
    def __init__(self, base_url: str = "https://html.duckduckgo.com", proxy_url: str | None = None):
        self.base_url = base_url
        self.proxy_url = proxy_url or config.proxy_url_resolved
        self.client = httpx.AsyncClient(
            proxy=self.proxy_url,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        )

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        params = {"q": query, "kl": "us-en"}
        try:
            response = await self.client.get(f"{self.base_url}/html/", params=params)
            response.raise_for_status()

            html = response.text

            if self._is_captcha(html):
                logger.warning("DDG returned CAPTCHA page")
                return [{"title": "Search blocked", "snippet": "DuckDuckGo is blocking automated requests. Please try a different search query or use a different search engine.", "link": ""}]

            results = []

            link_pattern = re.compile(
                r'<a[^>]*class="result__snippet"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            )
            title_pattern = re.compile(
                r'<a[^>]*class="result__url"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
            )
            title_pattern2 = re.compile(
                r'<h2[^>]*class="result__title"[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]*)</a></h2>'
            )

            snippets = link_pattern.findall(html)
            urls = title_pattern.findall(html)
            titles2 = title_pattern2.findall(html)

            for i, (url, snippet) in enumerate(snippets[:num_results]):
                title = ""
                if i < len(urls):
                    title = urls[i][1]
                if not title and i < len(titles2):
                    title = titles2[i][1]
                if not title:
                    title = "Result"

                clean_url = url.replace("&", "&")
                if clean_url.startswith("//duckduckgo.com/l/?uddg="):
                    clean_url = "https:" + clean_url

                results.append({
                    "title": title.strip(),
                    "snippet": snippet.strip(),
                    "link": clean_url,
                })

            return results

        except httpx.RequestError as e:
            logger.error(f"DDG request failed: {e}")
            return [{"title": "Search error", "snippet": f"Failed to search: {e}", "link": ""}]
        except httpx.HTTPStatusError as e:
            logger.error(f"DDG HTTP error: {e}")
            return [{"title": "Search error", "snippet": f"Search returned error: {e.response.status_code}", "link": ""}]
        except Exception as e:
            logger.error(f"DDG search error: {e}")
            return [{"title": "Search error", "snippet": f"Unexpected error: {e}", "link": ""}]

    def _is_captcha(self, html: str) -> bool:
        captcha_indicators = [
            "Unfortunately, bots use DuckDuckGo too",
            "Please complete the following challenge",
            "anomaly-modal",
            "Select all squares containing a duck",
        ]
        return any(indicator in html for indicator in captcha_indicators)

    async def close(self):
        await self.client.aclose()