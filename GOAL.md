# infosec-plugins — Goal & Plugin Roadmap

The **curated marketplace** for [`infosec-cli`](https://github.com/ModelsLab/infosec-cli).
Every `infosec` CLI auto-syncs this repo on startup, so **adding a security tool = a PR here, never a change to the CLI codebase.**

> **North star:** keep the CLI binary lean. Ship *no* security tooling compiled in (beyond a thin default profile + bundled skills). All tools/MCP/methodology live here as installable, toggleable content. Adding, updating, or removing a plugin must require **zero Rust changes and no CLI release** — only a push to this repo.

---

## 1. How this repo reaches every CLI (verified against CLI source)

On startup the CLI runs a curated-plugins sync (`codex-rs/core-plugins/src/startup_sync.rs`):
1. `git ls-remote https://github.com/ModelsLab/infosec-plugins.git HEAD` → resolves the default-branch commit.
2. Shallow-fetches that commit into `~/.infosec/.tmp/plugins/` (sha tracked in `.tmp/plugins.sha`; only re-syncs on change).
3. **Requires `.agents/plugins/marketplace.json` at the repo root** or the sync is rejected.
4. Fallbacks: GitHub REST zipball → (dead OpenAI export path, ignored).

**Contract:**
- Default branch (`main`) HEAD must always contain a valid `.agents/plugins/marketplace.json`.
- `refs/codex/curated-sync` is a *local* ref name inside the CLI — this repo needs **no** special ref/branch, just `main`.
- **Push to `main` → live on every CLI at next launch.** No CLI rebuild.

> **CLI status:** the sync URL is now repointed to `ModelsLab/infosec-plugins` (`startup_sync.rs:24-26,601`). This ships to users on the next CLI **release build**; until then, users can consume this repo manually with `infosec plugin marketplace add <git-or-path>` (tested working).

---

## 2. Repo layout

```
.agents/plugins/marketplace.json      # catalog (REQUIRED, repo root, default branch)
.agents/plugins/api_marketplace.json  # identical copy (api-curated consumer)
plugins/<name>/.codex-plugin/plugin.json    # per-plugin manifest
plugins/<name>/skills/<skill>/SKILL.md      # optional skill pack (pure knowledge)
plugins/<name>/.mcp.json                     # optional MCP server(s)
third_party/<name>/LICENSE                    # verbatim upstream license for anything vendored
```

### marketplace.json (verified shape)
```json
{
  "name": "infosec",
  "interface": { "displayName": "InfoSec Toolkit" },
  "plugins": [
    { "name": "recon-nmap",
      "source": { "source": "local", "path": "./plugins/recon-nmap" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_USE" },
      "category": "reconnaissance" }
  ]
}
```
- `installation`: `INSTALLED_BY_DEFAULT` (auto-installs) · `AVAILABLE` (opt-in via `infosec plugin add`) · `NOT_AVAILABLE`.
- `authentication`: `ON_INSTALL` · `ON_USE`. **There is no `NONE`.**
- `source`: `{"source":"local","path":"./…"}` · `{"source":"url","url":"owner/repo"}` · `git-subdir` · `npm`. **No `github` variant.**
- `category` drives the CLI's (upcoming) category enable/disable filter; it is safe to set today (ignored until the feature ships).

### plugin.json (verified shape)
```json
{
  "name": "recon-nmap",
  "version": "0.1.0",
  "description": "…",
  "keywords": ["recon","nmap"],
  "skills": "./skills",                 // optional dir of SKILL.md
  "mcpServers": "./.mcp.json",          // optional; path OR inline object
  "interface": { "displayName": "Nmap (recon)", "category": "reconnaissance", "capabilities": ["execute"] }
}
```

---

## 3. Packaging patterns for code-bearing plugins (READ THIS)

**Installing a plugin downloads the whole plugin directory into `~/.infosec/plugins/cache/<mkt>/<plugin>/<version>/` (verified). But the CLI does NOT install dependencies or provide a runtime** — it only runs the MCP server's `command`. There is also **no `${PLUGIN_ROOT}` templating**, and the server's working dir defaults to the session cwd, not the plugin folder.

⟹ **Never ship a loose `server.py` + `requirements.txt` and expect it to run.** The files arrive, but it crashes on missing deps / wrong cwd. Instead, the code + deps must come from a registry the `command` pulls at launch:

| Pattern | `.mcp.json` command | Use for | Requires on host |
|---|---|---|---|
| **Docker** (preferred for heavy/offensive tools) | `docker run --rm -i <image>` | tool wrappers, anything with system deps | Docker |
| **uvx** | `uvx --from git+https://… <entry>` | pure-Python MCP servers (PyPI or git) | `uv` |
| **npx** | `npx -y @scope/pkg` | JS MCP servers | Node |
| **Wrapped host binary** | `nmap` / `medusa` … | shell out to an already-installed CLI | that binary |
| **Skill pack** (no code) | — (just `SKILL.md`) | methodology / prompts | nothing |

> **Recommendation:** for Docker-based tools we adopt, **ModelsLab publishes the built images to GHCR** (`ghcr.io/modelslab/<tool>-mcp`) so `docker run` "just works" (pullable). Otherwise the plugin README must tell users to build the image first (see mcp-security-hub below — its images are build-from-source only).

---

## 4. Category taxonomy (for enable/disable-by-category)

Free-form string, soft-validated (unknown categories warn, never fail to load).

**Primary:** `reconnaissance` · `web` · `exploitation` · `osint` · `reverse-engineering` · `mobile` · `reporting` · `threat-intel` · `agent-framework`
**Extended:** `cloud` · `code-security` · `secrets` · `fuzzing` · `password-cracking` · `active-directory` · `credential-testing`

---

## 5. Source-repo → plugin plan

### 5.0 Extraction philosophy — lift the engine, drop the shell

For every source repo we **cut straight to the functional core and discard the scaffolding.** A tool like robin is 90% UI + service glue + its own LLM layer; the actual value is 1–2 modules that do the work. The process:

1. **Find the engine** — the module(s) that perform the real capability (network calls, parsing, tool orchestration), independent of any UI/web-server/DB.
2. **Discard the shell** — Streamlit/React UI, session state, persistence panels, auth/config screens, telemetry, packaging scaffolding.
3. **Discard the repo's own LLM calls** — our CLI agent is already the model. Wrapping an in-repo LLM step as a tool means a second, weaker model behind the first (double cost/latency). Expose the raw capability (search, scrape, scan) and let the agent do the reasoning (refine, filter, report) itself.
4. **Wrap the lifted engine in a thin stdio MCP `server.py`** exposing a few clean tools; ship the code + deps via a registry the `command` pulls (uvx-from-git / Docker / GHCR — never loose files, per §3).
5. **Respect the license** (§8): MIT/Apache → lift + attribute under `third_party/<name>/`. AGPL/non-commercial/closed → you may **not** copy the engine; wrap the installed binary as a subprocess, or clean-room re-implement the idea in native code.

**Worked example — robin (see `plugins/darkweb-osint/`):** lift `search.py` (16-onion-engine fan-out over Tor SOCKS5) + `scrape.py` (Tor page fetch, 1 MB cap) + a Tor health check; discard `ui.py`, `investigations/` persistence, and all of `llm.py`/`llm_utils.py`/`config.py`. Result: a 4-tool MCP server (`tor_status`, `darkweb_search`, `darkweb_scrape`, `darkweb_scrape_many`), 4 deps (`requests`, `PySocks`, `beautifulsoup4`, `mcp`), **zero API keys** (LLM steps dropped). The agent runs refine→search→filter→scrape→report as its own loop.

### 5.1 Per-repo plan

Verified licenses + distribution facts. **Legal rule: MIT/Apache may be lifted + attributed; AGPL and non-commercial code is subprocess- or reference-only, never vendored.**

| Source repo | License | What we take | Packaging | Category | Public repo? | Notes (verified) |
|---|---|---|---|---|---|---|
| **FuzzingLabs/mcp-security-hub** | **MIT** | First-party tool servers: **nmap, nuclei, ffuf**, whatweb, masscan, sqlmap, waybackurls, binwalk, yara, capa, gitleaks, searchsploit | **Docker MCP plugins** | recon / web / RE / secrets / exploitation | ✅ catalog+wrappers | Images are **build-from-source only** (no Docker Hub/GHCR). → **we republish to `ghcr.io/modelslab/<tool>-mcp`** so installs pull cleanly. **nmap/masscan need `--cap-add=NET_RAW`**; nuclei/ffuf don't; no API keys. **Avoid** its GPL wrappers (burp) and third-party-repo wrappers. |
| **apurvsinghgautam/robin** | **MIT** | **Lift the engine:** `search.py` (fan-out across 16 hardcoded onion search engines over Tor SOCKS5) + `scrape.py` (Tor page fetch, 1 MB cap, HTML→text) + Tor health check. **Discard** `ui.py`, `investigations/` persistence, and `llm.py`/`llm_utils.py`/`config.py` (the whole LLM layer). | **stdio MCP plugin** `darkweb-osint` — thin `server.py` over the lifted engine; tools `tor_status`, `darkweb_search`, `darkweb_scrape`, `darkweb_scrape_many`. Deps: requests, PySocks, beautifulsoup4, mcp. **No API keys.** | osint / threat-intel | ⚠️ authorized-use + prefer backend-gated | Launch via `uvx --from git+…#subdirectory=plugins/darkweb-osint`. Runtime prereq: **Tor daemon on `127.0.0.1:9050`** (`tor_status` gate). Agent does refine/filter/report itself. Attribution → `third_party/robin/`. |
| **Pantheon-Security/medusa** | **AGPL-3.0** | LLM/agent-config security **scanning** as an interop target (SARIF ingest) | **Subprocess wrapper** (user installs `medusa`; we shell out, parse SARIF) — **no code vendored** | code-security / secrets | ✅ wrapper only | AGPL ⇒ embedding triggers source-disclosure; keep as a separate program invoked over CLI. Pin exact PyPI/brew name + flags at impl. |
| **aliasrobotics/cai** | **Research-Use (non-commercial) + MIT** | **Ideas only, clean-room:** kill-chain tool taxonomy, category-tagged registry, command guardrails (homograph/base64/dangerous-pattern), HITL interrupt | **Reference-only** → native CLI features, not a marketplace plugin | agent-framework | ❌ not vendored | Non-commercial license **bars** bundling in a commercial product. Re-implement equivalents in Rust; copy no source/prompts. |
| **google/sec-gemini** | **Apache-2.0 (clients); model closed** | Session/threading/usage **schema** as a template; permissioned local-tool-exec UX | **Reference-only** | threat-intel / defensive | ❌ not a plugin | Capability is a **closed hosted model** (`api.secgemini.google`) — cannot vendor/self-host. Feeds the CLI↔backend design, not this repo. |

**Extensible by design:** more repos later follow the same flow — no new plugin *types* needed. If a tool is a CLI binary → wrapper plugin; a Python/JS MCP → docker/uvx/npx plugin; pure knowledge → skill pack.

### First real plugins to build (all MIT, license-clean)
1. **`darkweb-osint`** — ✅ built (this repo): robin engine lifted into a stdio MCP server. Launchable once pushed (uvx-from-git) with Tor running.
2. `recon-nmap`, `web-nuclei`, `web-ffuf` — Docker MCP plugins (after we publish images to `ghcr.io/modelslab/<tool>-mcp`). nmap manifest carries `--cap-add=NET_RAW`.
3. `codesec-medusa` — subprocess wrapper (AGPL-safe).

---

## 6. How to add a new plugin (pure content — no codebase change)

1. `mkdir -p plugins/<name>/.codex-plugin` and write `plugin.json` (§2).
2. Add capability: `skills/<skill>/SKILL.md` (knowledge) and/or `.mcp.json` (a docker/uvx/npx/binary launch, §3).
3. If vendoring MIT/Apache code, drop the upstream `LICENSE` under `third_party/<name>/`.
4. Register it in `.agents/plugins/marketplace.json` **and** `api_marketplace.json` (name, `source` local path, `policy`, `category`).
5. Test locally: `infosec plugin marketplace add $(pwd)` → `infosec plugin add <name>@infosec` → confirm install + (for MCP) that the server launches.
6. Commit + push `main`. Live on all CLIs next launch.

---

## 7. CLI-side readiness (what makes future plugins codebase-free)

| Item | Status | Needed for |
|---|---|---|
| Sync URL → `ModelsLab/infosec-plugins` (`startup_sync.rs:24-26,601`) | ✅ done (this change) | Auto-appearing plugins on every CLI |
| Ship the repointed binary (release build) | ⬜ pending | Users get auto-sync without manual `marketplace add` |
| Plugin install / toggle / marketplace-add | ✅ works today (tested) | Adding/enabling plugins with no code change |
| **Category enable/disable feature** (M1–M4) | ⬜ next codebase change | Toggling whole categories on/off; see `infosec-cli/MARKETPLACE-PLAN.md` |
| De-brand: `OPENAI_*` consts → `INFOSEC_*`, `~/.codex`→`~/.infosec` | ⬜ M0 | Coherent naming |

**Principle:** once the repointed binary ships, plugin content (incl. `category` strings) needs no Rust change. The *only* remaining codebase change is the category-**toggle feature** itself (a thin metadata+filter layer, fully specced in `MARKETPLACE-PLAN.md`). Plugins should carry `category` now so they're ready the day it lands.

---

## 8. Legal & safety rules

- **Licenses:** MIT/Apache → wrap + attribute under `third_party/`. AGPL/GPL → subprocess or reference-only, never bundled. Non-commercial/closed → reference/clean-room only.
- **No weaponized payloads in this public repo** — plugins wrap tools that pull published images/packages or shell out to user-installed binaries. Genuinely offensive/sensitive content belongs behind the authenticated backend catalog (`/ps/plugins/*`), not here.
- **Authorized-use framing** on offensive/OSINT/dark-web skills; runtime prereq checks (Docker, Tor) with clear errors.
- **Data egress:** flag any plugin that sends scraped/target content to the model backend.
