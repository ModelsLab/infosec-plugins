# Adapted from robin (https://github.com/apurvsinghgautam/robin)
# MIT License — Copyright (c) 2025 Apurv Singh Gautam. See third_party/robin/LICENSE.
# Streamlit/LLM layers not carried over. This is robin's Tor scraper only.
"""Fetch and text-extract pages over Tor (.onion) or clearnet."""
from __future__ import annotations

import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"
MAX_DOWNLOAD_BYTES = 1_000_000
MAX_EXTRACTED_TEXT_CHARS = 50_000
MAX_RETURN_CHARS = 2_000
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")

_local = threading.local()


def _build_session(use_tor: bool) -> requests.Session:
    session = requests.Session()
    if use_tor:
        session.proxies = {"http": TOR_SOCKS_PROXY, "https": TOR_SOCKS_PROXY}
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _get_session(use_tor: bool) -> requests.Session:
    """Thread-local session cache (one Tor + one direct session per worker thread)."""
    cache = getattr(_local, "sessions", None)
    if cache is None:
        cache = {}
        _local.sessions = cache
    key = "tor" if use_tor else "direct"
    if key not in cache:
        cache[key] = _build_session(use_tor)
    return cache[key]


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string if soup.title and soup.title.string else "").strip()
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()[:MAX_EXTRACTED_TEXT_CHARS]
    return f"{title} - {text}".strip(" -")


def scrape_single(url_data: dict) -> tuple[str, str]:
    """Fetch one URL; auto-route through Tor when the host ends in .onion. Returns (url, text)."""
    url = url_data.get("link") or url_data.get("url") or ""
    host = (urlparse(url).hostname or "").lower()
    use_tor = host.endswith(".onion")
    timeout = (10, 45) if use_tor else (5, 25)
    session = _get_session(use_tor)
    try:
        resp = session.get(url, stream=True, timeout=timeout)
        resp.raise_for_status()
        ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if ctype and not ctype.startswith(ALLOWED_CONTENT_TYPES):
            return url, ""
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_content(chunk_size=8192):
            if not chunk:
                continue
            total += len(chunk)
            chunks.append(chunk)
            if total >= MAX_DOWNLOAD_BYTES:
                break
        body = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")
    except requests.RequestException as exc:
        return url, f"[error: {exc}]"
    return url, _extract_text(body)


def scrape_multiple(urls_data: list[dict], max_workers: int = 5) -> dict:
    """Concurrent scrape; dedupe by url; truncate each result to MAX_RETURN_CHARS."""
    out: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(scrape_single, item) for item in urls_data]
        for future in as_completed(futures):
            url, text = future.result()
            if url in out:
                continue
            out[url] = text[:MAX_RETURN_CHARS]
    return out
