# infosec-cli plugins (curated marketplace)

Curated marketplace of security **skills**, **tool wrappers**, and **MCP servers** for
[`infosec-cli`](https://github.com/ModelsLab/infosec-cli).

Every `infosec` CLI auto-syncs this repo on startup (`git ls-remote HEAD` → shallow fetch →
cached under `~/.infosec/.tmp/plugins`). **Push to the default branch → all CLIs pick it up on
next launch.** No CLI release required.

## Layout

```
.agents/plugins/marketplace.json      # catalog (required, at repo root, on default branch)
.agents/plugins/api_marketplace.json  # same content (consumed by the api-curated path)
plugins/<name>/.codex-plugin/plugin.json   # per-plugin manifest
plugins/<name>/skills/<skill>/SKILL.md     # optional skill pack
plugins/<name>/.mcp.json                   # optional MCP server(s)
```

## Packaging tiers

| Tier | Ships | Example |
|---|---|---|
| Skill pack | `skills/` dir of `SKILL.md` methodology | `pentest-recon` |
| MCP server | `.mcp.json` (stdio `command`/`docker run -i` or remote) | `web-nuclei` |
| Wrapped tool | thin MCP server shelling to a host binary | (brutespray, medusa, …) |

## Rules
- `installation`: `INSTALLED_BY_DEFAULT` (auto) · `AVAILABLE` (opt-in via `infosec plugin add`) · `NOT_AVAILABLE`.
- `authentication`: `ON_INSTALL` · `ON_USE`. (There is **no** `NONE`.)
- `category` drives the CLI's category enable/disable filter.
- Keep **weaponized payloads out of this public repo** — wrap already-installed local binaries only. Route offensive/sensitive content through the authenticated backend catalog.
- Vendored third-party code keeps its `LICENSE`; AGPL/GPL/non-commercial code is subprocess- or reference-only, never bundled.
