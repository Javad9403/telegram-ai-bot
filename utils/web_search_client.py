import logging
import re
import httpx

logger = logging.getLogger(__name__)


class DuckDuckGoClient:
    def __init__(self, base_url: str = "https://html.duckduckgo.com"):
        self.base_url = base_url

    async def search(self, query: str, num_results: int = 10) -> list[dict]:
        params = {"q": query}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, data=params)
                response.raise_for_status()

                html = response.text
                results = []

                link_pattern = re.compile(
                    r'<a[^>]*class="result__snippet"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                )
                title_pattern = re.compile(
                    r'<a[^>]*class="result__url"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                )

                snippets = link_pattern.findall(html)
                urls = title_pattern.findall(html)

                for i, (url, snippet) in enumerate(snippets[:num_results]):
                    title = urls[i][1] if i < len(urls) else "Result"
                    clean_url = url.replace("&", "&")
                    if clean_url.startswith("//duckduckgo.com/l/?uddg="):
                        clean_url = "https:" + clean_url

                    results.append({
                        "title": title.strip(),
                        "snippet": snippet.strip(),
                        "link": clean_url,
                    })

                if not results:
                    result_pattern = re.compile(
                        r'<a[^>]*class="result__snippet"[^>]*href="([^"]*)"[^>]*>([^<]*)</a>'
                    )
                    title_pattern2 = re.compile(
                        r'<h2[^>]*class="result__title"[^>]*><a[^>]*href="([^"]*)"[^>]*>([^<]*)</a></h2>'
                    )

                    snippets2 = result_pattern.findall(html)
                    titles = title_pattern2.findall(html)

                    for i, (url, snippet) in enumerate(snippets2[:num_results]):
                        title = titles[i][1] if i < len(titles) else "Result"
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
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"DDG HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"DDG search error: {e}")
            return []