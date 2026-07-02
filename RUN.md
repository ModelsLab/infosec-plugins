# RUN — infosec-plugins (test, run, add, publish)

Runnable quickstart for the curated marketplace. Full plan: `GOAL.md`.
Exercised end-to-end against a freshly built `infosec` CLI on macOS.

Set the CLI path once:
```bash
BIN=~/Documents/projects/infosec-cli/codex-rs/target/debug/infosec   # build it first (see CLI RUN.md)
```

## 1. Test the marketplace against the CLI (no push needed)
```bash
export INFOSEC_HOME=/tmp/inf-test           # throwaway home
$BIN plugin marketplace add "$PWD"          # add THIS repo as a local marketplace
$BIN plugin list                            # → pentest-recon, pentest-report, web-nuclei, darkweb-osint
$BIN plugin add pentest-report@infosec      # skill pack — installs instantly
```
Already pushed to `main`, so the auto-sync path also serves it with no `marketplace add` at all
(see the CLI `RUN.md` §3A).

## 2. Run the `darkweb-osint` plugin
Exposes 4 MCP tools (`tor_status`, `darkweb_search`, `darkweb_scrape`, `darkweb_scrape_many`).
Engine lifted from robin (MIT, see `third_party/robin/LICENSE`); the agent does the LLM reasoning.

### Prereqs are installed for you (install-time preflight)
`darkweb-osint` declares `tor` + `uv` in its marketplace entry (§3, `requirements`). Installing the
plugin **auto-installs them per-OS and hard-fails if it can't** — you never get a half-working plugin:
```bash
$BIN plugin add darkweb-osint@infosec
#   ↳ [darkweb-osint@infosec] prerequisite `tor` not found — installing: brew install tor && brew services start tor
#   ... 🍺 tor 0.4.9.11 ... Successfully started `tor` ...
#   ↳ [darkweb-osint@infosec] `tor` is now available.
#   Added plugin `darkweb-osint` from marketplace `infosec`.
```
- `INFOSEC_PLUGIN_PREREQS=check` → verify only, hard-fail if missing (no install).
- `INFOSEC_PLUGIN_PREREQS=skip`  → bypass the check.

The preflight guarantees the `tor` **binary**; the daemon must be **running** on `127.0.0.1:9050`
(the macOS installer starts it via `brew services`). Confirm:
```bash
brew services list | grep tor          # → tor  started
```

### Smoke-test the engine directly (no MCP client needed)
```bash
# Tor reachable? (verified → {'status': 'up', 'latency_ms': 2, 'error': None})
uv run --project plugins/darkweb-osint python -c "from robin_mcp import health; print(health.check_tor_proxy())"

# Live onion search (needs Tor 'up'; onion engines are slow/flaky, expect a partial set):
uv run --project plugins/darkweb-osint python -c \
  "from robin_mcp import search; import json; print(json.dumps(search.get_search_results('ransomware leak site')[:3], indent=2))"
```

### Run it inside the CLI agent
```bash
$BIN plugin add darkweb-osint@infosec
$BIN "use tor_status to confirm Tor, then darkweb_search leak sites for <authorized-target> and scrape the top hit"
```
The MCP server is launched by `.mcp.json` via (works now that this repo is pushed):
```
uvx --from "git+https://github.com/ModelsLab/infosec-plugins.git#subdirectory=plugins/darkweb-osint" darkweb-mcp
```
> Authorized threat-intel / OSINT use only.

## 3. Add a new plugin (pure content — no CLI rebuild)
Skill-pack example (this is exactly how `pentest-report` was added):
```bash
mkdir -p plugins/<name>/.codex-plugin plugins/<name>/skills/<skill>
# plugins/<name>/.codex-plugin/plugin.json   → name, version, "skills":"./skills", interface.category
# plugins/<name>/skills/<skill>/SKILL.md      → frontmatter (name, description, metadata.category) + body
# register it in BOTH .agents/plugins/marketplace.json and api_marketplace.json (keep them identical)
$BIN plugin marketplace add "$PWD" && $BIN plugin add <name>@infosec   # test
```

### Declaring system prerequisites (the install-time preflight)
Add a top-level `requirements` block to the plugin's **marketplace entry** so the CLI installs its
deps at `plugin add` time (and refuses to install if it can't):
```json
{
  "name": "web-nuclei",
  "source": { "source": "local", "path": "./plugins/web-nuclei" },
  "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
  "category": "web",
  "requirements": {
    "tools": [
      {
        "command": "docker",                       // must resolve on PATH
        "install": {                                // optional; per std::env::consts::OS
          "macos":   "brew install --cask docker",
          "linux":   "curl -fsSL https://get.docker.com | sh",
          "windows": "winget install -e --id Docker.DockerDesktop"
        },
        "hint": "Start Docker Desktop, then retry."  // shown if it can't be auto-installed
      }
    ]
  }
}
```
Omit `install` for a check-only prereq (hard-fails with the `hint` if the command is missing —
that's how `web-nuclei` gates on `docker`).

## 4. Publish (go live on every CLI)
```bash
git add -A
git commit -m "add <plugin>"
git push origin main
```
Every `infosec` CLI running the repointed binary auto-syncs `main` on next launch.

## Status
- ✅ Marketplace tested against the CLI (add / list / install / enable / disable / remove).
- ✅ `darkweb-osint`: preflight auto-installed `tor` (real `brew install`), Tor proxy up, engine `health` = up.
- ✅ New plugin `pentest-report` (reporting skill pack) authored, registered, installed.
- ✅ `pentest-recon` skill works; `web-nuclei` gates on `docker` (template pending a GHCR image).
- Published to `main` (auto-sync verified). `.venv`/`__pycache__` are git-ignored — the plugin is
  built from source via `uvx`, never from a committed venv.
