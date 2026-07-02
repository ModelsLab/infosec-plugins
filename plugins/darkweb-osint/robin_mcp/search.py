# Adapted from robin (https://github.com/apurvsinghgautam/robin)
# MIT License — Copyright (c) 2025 Apurv Singh Gautam. See third_party/robin/LICENSE.
# The Streamlit UI, investigation persistence, and LLM layers are intentionally NOT
# carried over. This is robin's search engine only, exposed headlessly for an MCP agent.
"""Fan-out search across Tor onion search engines."""
from __future__ import annotations

import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
]

# 16 onion search engines (verbatim from robin's search.py SEARCH_ENGINES).
SEARCH_ENGINES = [
    {"name": "Ahmia", "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}"},
    {"name": "OnionLand", "url": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/search?q={query}"},
    {"name": "Torgle", "url": "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion/torgle/?query={query}"},
    {"name": "Amnesia", "url": "http://amnesia7u5odx5xbwtpnqk3edybgud5bmiagu75bnqx2crntw5kry7ad.onion/search?query={query}"},
    {"name": "Kaizer", "url": "http://kaizerwfvp5gxu6cppibp7jhcqptavq3iqef66wbxenh6a2fklibdvid.onion/search?q={query}"},
    {"name": "Anima", "url": "http://anima4ffe27xmakwnseih3ic2y7y3l6e7fucwk4oerdn4odf7k74tbid.onion/search?q={query}"},
    {"name": "Tornado", "url": "http://tornadoxn3viscgz647shlysdy7ea5zqzwda7hierekeuokh5eh5b3qd.onion/search?q={query}"},
    {"name": "TorNet", "url": "http://tornetupfu7gcgidt33ftnungxzyfq2pygui5qdoyss34xbgx2qruzid.onion/search?q={query}"},
    {"name": "Torland", "url": "http://torlbmqwtudkorme6prgfpmsnile7ug2zm4u3ejpcncxuhpu4k2j4kyd.onion/index.php?a=search&q={query}"},
    {"name": "Find Tor", "url": "http://findtorroveq5wdnipkaojfpqulxnkhblymc7aramjzajcvpptd4rjqd.onion/search?q={query}"},
    {"name": "Excavator", "url": "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/search?query={query}"},
    {"name": "Onionway", "url": "http://oniwayzz74cv2puhsgx4dpjwieww4wdphsydqvf5q7eyz4myjvyw26ad.onion/search.php?s={query}"},
    {"name": "Tor66", "url": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/search?q={query}"},
    {"name": "OSS", "url": "http://3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion/oss/index.php?search={query}"},
    {"name": "Torgol", "url": "http://torgolnpeouim56dykfob6jh5r2ps2j73enc42s2um4ufob3ny4fcdyd.onion/?q={query}"},
    {"name": "The Deep Searches", "url": "http://searchgf7gdtauh7bhnbyed4ivxqmuoat3nm6zfrg3ymkq6mtnpye3ad.onion/search?q={query}"},
]

_ONION_RE = re.compile(r"https?://[a-z2-7]{16,56}\.onion\S*", re.IGNORECASE)


def get_tor_session() -> requests.Session:
    """A requests session routed through the local Tor SOCKS5 proxy (socks5h = DNS via Tor)."""
    session = requests.Session()
    session.proxies = {"http": TOR_SOCKS_PROXY, "https": TOR_SOCKS_PROXY}
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_search_results(endpoint: str, query: str) -> list[dict]:
    """Query ONE engine endpoint; parse anchor tags; return [{'title','link'}]."""
    url = endpoint.replace("{query}", requests.utils.quote(query))
    session = get_tor_session()
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        resp = session.get(url, headers=headers, timeout=40)
        resp.raise_for_status()
    except requests.RequestException:
        return []

    results: list[dict] = []
    soup = BeautifulSoup(resp.text, "html.parser")
    for anchor in soup.find_all("a", href=True):
        match = _ONION_RE.search(anchor["href"])
        if not match:
            continue
        link = match.group(0)
        if "search" in link.lower():
            continue
        title = anchor.get_text(strip=True)
        if len(title) <= 3:
            continue
        results.append({"title": title, "link": link})
    return results


def get_search_results(refined_query: str, max_workers: int = 5) -> list[dict]:
    """Fan out across all engines concurrently; dedupe by link. Primary entrypoint."""
    seen: set[str] = set()
    unique: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(fetch_search_results, e["url"], refined_query) for e in SEARCH_ENGINES]
        for future in as_completed(futures):
            for item in future.result():
                key = item["link"].rstrip("/")
                if key in seen:
                    continue
                seen.add(key)
                unique.append(item)
    return unique
