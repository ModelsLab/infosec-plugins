# RUN — infosec-plugins (test, run, add, publish)

Runnable quickstart for the curated marketplace. Full plan: `GOAL.md`.

Set the CLI path once:
```bash
BIN=~/Documents/projects/infosec-cli/codex-rs/target/debug/infosec   # build it first (see CLI RUN.md)
```

## 1. Test the marketplace against the CLI (no push needed)
```bash
export INFOSEC_HOME=/tmp/inf-test           # throwaway home
$BIN plugin marketplace add "$PWD"          # add THIS repo as a local marketplace
$BIN plugin list                            # → pentest-recon, web-nuclei, darkweb-osint
$BIN plugin add darkweb-osint@infosec       # install
```

## 2. Run the `darkweb-osint` plugin
It exposes 4 MCP tools (`tor_status`, `darkweb_search`, `darkweb_scrape`, `darkweb_scrape_many`).
Engine lifted from robin (MIT, see `third_party/robin/LICENSE`); the agent does the LLM reasoning.

### Prereqs
```bash
# macOS
brew install tor && brew services start tor
# Linux/WSL
# sudo apt install tor && sudo service tor start
# uv is required by the launch command (uvx). Check: uv --version
```

### Smoke-test the engine directly (no MCP client needed)
```bash
# Tor reachable?
uv run --project plugins/darkweb-osint python -c "from robin_mcp import health; print(health.check_tor_proxy())"
# → {'status': 'up', 'latency_ms': ..., 'error': None}

# Live onion search (needs Tor 'up'):
uv run --project plugins/darkweb-osint python -c "from robin_mcp import search; import json; print(json.dumps(search.get_search_results('ransomware leak site')[:3], indent=2))"
```

### Run it inside the CLI agent
```bash
$BIN plugin add darkweb-osint@infosec        # with Tor running
$BIN "use darkweb_search to find leak sites mentioning <authorized-target>, then darkweb_scrape the top hit"
```
The MCP server is launched by `.mcp.json` via:
```
uvx --from "git+https://github.com/ModelsLab/infosec-plugins.git#subdirectory=plugins/darkweb-osint" darkweb-mcp
```
That git URL resolves **only after you push** (step 4). Until then, use local install (step 1) — but
note the uvx-from-git launch also needs the push, so to exercise the live tools either push first or
temporarily point `.mcp.json` at a local path.

> Authorized threat-intel / OSINT use only.

## 3. Add a new plugin (pure content — no CLI rebuild)
```bash
mkdir -p plugins/<name>/.codex-plugin
# write plugins/<name>/.codex-plugin/plugin.json  (name, category, skills and/or mcpServers)
# add skills/<skill>/SKILL.md  and/or  .mcp.json  (docker/uvx/npx/binary — see GOAL.md §3)
# register it in BOTH .agents/plugins/marketplace.json and api_marketplace.json
$BIN plugin marketplace add "$PWD" && $BIN plugin add <name>@infosec   # test
```

## 4. Publish (go live on every CLI)
```bash
git add -A
git commit -m "add <plugin>"
git push origin main
```
Every `infosec` CLI running the repointed binary auto-syncs `main` on next launch.

## Status
- Built + validated: `darkweb-osint` (CLI install ✅, `uv` build+import ✅).
- `pentest-recon` (skill) works; `web-nuclei` is a template pending a GHCR image.
- Nothing pushed yet.
