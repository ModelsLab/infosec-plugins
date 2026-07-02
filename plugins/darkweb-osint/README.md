# darkweb-osint

Headless **dark-web OSINT** for [`infosec-cli`](https://github.com/ModelsLab/infosec-cli).
It exposes robin's Tor search-and-scrape **engine** to the agent over stdio MCP — the
Streamlit UI and robin's own LLM layer are dropped; the driving agent (the model) does the
query refinement, filtering, and reporting itself.

> ⚠️ **Authorized threat-intel / OSINT use only.** Accessing hidden services may be
> regulated in your jurisdiction. Only query and fetch what you are authorized to, on
> engagements you have permission to run.

---

## Tools

| Tool | Purpose |
|---|---|
| `tor_status` | Check the local Tor SOCKS5 proxy (`127.0.0.1:9050`). **Call this first.** |
| `darkweb_search(query, max_results=20)` | Fan a query across **16 onion search engines** over Tor. Returns `[{title, link}]`. |
| `darkweb_scrape(url)` | Fetch + text-extract one `.onion` (or clearnet) page over Tor. Returns `{url, text}` (text hard-capped). |
| `darkweb_scrape_many(urls, max_workers=5)` | Concurrently fetch multiple pages. Returns `{url: text}`. |

The LLM steps (query refinement, relevance filtering, summarization) are intentionally **not**
exposed as tools — the agent is already a model and should do that reasoning itself.

---

## Prerequisites (installed automatically)

This plugin declares its prerequisites in the marketplace, so **`infosec plugin add
darkweb-osint@infosec` checks for them and installs the missing ones before the plugin is
registered.** If a prerequisite is missing and cannot be installed, the install **aborts** and
the plugin is *not* added — you never end up with a half-working plugin.

| Prereq | Why | Auto-install |
|---|---|---|
| **`uv`** | Provides the `uvx` launcher the MCP server runs under. | `curl -LsSf https://astral.sh/uv/install.sh \| sh` (macOS/Linux) · `irm https://astral.sh/uv/install.ps1 \| iex` (Windows) — user-space, no sudo. |
| **`tor`** | A local Tor SOCKS5 proxy on `127.0.0.1:9050` for all requests. | `brew install tor && brew services start tor` (macOS) · `sudo apt-get install -y tor && sudo service tor start` (Linux) · `choco install -y tor` (Windows). |

Control the behavior with the `INFOSEC_PLUGIN_PREREQS` environment variable:

| Value | Behavior |
|---|---|
| *(unset)* / `install` | **Default.** Check, auto-install anything missing, re-check, hard-fail if still missing. |
| `check` | Only verify presence; never auto-install (still hard-fails if missing). |
| `skip` | Bypass the check entirely (install the plugin regardless). |

> The preflight guarantees the `tor` **binary** is installed; it does not guarantee the daemon
> is *running*. If the SOCKS proxy is down at run time, `tor_status` reports `{"status":"down"}`
> — start it with `brew services start tor` / `sudo service tor start`.

---

## How it launches

`.mcp.json` runs the server straight from git via `uvx`:

```
uvx --from "git+https://github.com/ModelsLab/infosec-plugins.git#subdirectory=plugins/darkweb-osint" darkweb-mcp
```

`uvx` builds an **isolated, ephemeral Python environment** and pulls the package + its Python
deps on first use — nothing is installed globally, and the plugin ships no vendored Python.

---

## Usage

Inside the CLI agent (Tor running):

```bash
infosec plugin add darkweb-osint@infosec
infosec "use tor_status to confirm Tor is up, then darkweb_search for leak sites mentioning <authorized-target> and scrape the top hit"
```

Smoke-test the engine directly (no MCP client needed):

```bash
# Tor reachable?
uv run --project plugins/darkweb-osint python -c \
  "from robin_mcp import health; print(health.check_tor_proxy())"
# → {'status': 'up', 'latency_ms': ..., 'error': None}

# Live onion search (needs Tor 'up'):
uv run --project plugins/darkweb-osint python -c \
  "from robin_mcp import search, json; print(search.get_search_results('ransomware leak site')[:3])"
```

---

## Attribution

The search/scrape engine is adapted from **[robin](https://github.com/apurvsinghgautam/robin)**
by Apurv Singh Gautam (MIT License). The 16-engine list and Tor session handling are lifted from
robin's `search.py`; the Streamlit UI, investigation persistence, and LangChain LLM layers are
**not** carried over. See [`third_party/robin/LICENSE`](../../third_party/robin/LICENSE) at the
repo root.
