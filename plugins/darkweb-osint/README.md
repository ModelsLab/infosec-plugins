# darkweb-osint

Headless dark-web OSINT for `infosec-cli`. Exposes robin's Tor search/scrape **engine** over
stdio MCP — the Streamlit UI and robin's own LLM layer are dropped; the driving agent does the
query refinement, filtering, and reporting itself.

> **Authorized threat-intel / OSINT use only.** Accessing hidden services may be regulated in
> your jurisdiction; only query and fetch what you are authorized to.

## Tools
| Tool | Purpose |
|---|---|
| `tor_status` | Check the local Tor SOCKS5 proxy (call first). |
| `darkweb_search(query, max_results=20)` | Fan-out across 16 onion search engines. Returns `[{title, link}]`. |
| `darkweb_scrape(url)` | Fetch + text-extract one `.onion`/clearnet page over Tor. |
| `darkweb_scrape_many(urls, max_workers=5)` | Concurrent fetch. Returns `{url: text}`. |

## Prerequisites
- **Tor daemon** on `127.0.0.1:9050` — `brew install tor && brew services start tor` (macOS) or
  `apt install tor && service tor start` (Linux/WSL).
- **`uv`** on PATH (the launch command is `uvx`). The server + its Python deps are fetched and
  run in an ephemeral environment on first use — nothing is installed globally.

## How it launches
`.mcp.json` runs `uvx --from git+https://github.com/ModelsLab/infosec-plugins.git#subdirectory=plugins/darkweb-osint darkweb-mcp`.
(Works once this repo is pushed; `uv` pulls the package straight from git.)

## Attribution
The search/scrape engine is adapted from **[robin](https://github.com/apurvsinghgautam/robin)**
by Apurv Singh Gautam, MIT License. See `third_party/robin/LICENSE` at the repo root.
