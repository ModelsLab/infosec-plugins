"""Headless stdio MCP server exposing robin's Tor search/scrape engine.

Authorized threat-intel / OSINT use only. Requires a local Tor daemon on 127.0.0.1:9050.
The LLM steps from robin (query refinement, filtering, summarization) are intentionally
NOT exposed as tools — the driving agent is already the model and should do that itself.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import health, scrape, search

mcp = FastMCP("robin-darkweb")


@mcp.tool()
def tor_status() -> dict:
    """Check the local Tor SOCKS5 proxy (127.0.0.1:9050). Call this BEFORE searching/scraping;
    if it is down, tell the user to start Tor (`brew services start tor` / `service tor start`)."""
    return health.check_tor_proxy()


@mcp.tool()
def darkweb_search(query: str, max_results: int = 20) -> list[dict]:
    """Fan a query out across 16 onion search engines over Tor. Returns [{'title','link'}].

    Refine the query yourself before calling. Authorized threat-intel/OSINT use only.
    """
    return search.get_search_results(query)[:max_results]


@mcp.tool()
def darkweb_scrape(url: str) -> dict:
    """Fetch and text-extract a single .onion (or clearnet) page over Tor. Returns {'url','text'}
    (text hard-capped). Only pass URLs you are authorized to access."""
    fetched_url, text = scrape.scrape_single({"link": url})
    return {"url": fetched_url, "text": text}


@mcp.tool()
def darkweb_scrape_many(urls: list[str], max_workers: int = 5) -> dict:
    """Concurrently fetch multiple pages over Tor. Returns {url: text}."""
    return scrape.scrape_multiple([{"link": u} for u in urls], max_workers)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
