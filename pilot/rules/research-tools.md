## Research Tools

### Search Priority

**⛔ Probe CLI first, always.** Finds by intent, not exact text. Instant results (<0.3s). Run via Bash.

**Fallback chain:** Probe CLI (`probe search`) → Grep/Glob (exact patterns) → Explore sub-agent (multi-step reasoning only)

Full Probe reference in `cli-tools.md`. Full MCP tool reference in `mcp-servers.md`.

### Tool Selection Guide

| Need | Tool | Notes |
|------|------|-------|
| **Codebase search** | **Probe CLI** (`probe search`) | Always first. Semantic, by intent. Run via Bash. |
| Exact pattern / known symbol | Grep / Glob | Only after Probe misses |
| Extract specific code block | Probe CLI (`probe extract`) | AST-aware, by line or symbol name |
| AST pattern matching | Probe CLI (`probe query`) | Find structural patterns (all functions, classes) |
| Library/framework docs | Context7 (MCP) | `resolve-library-id` → `query-docs` |
| Production code examples | grep-mcp (MCP) | Literal code patterns, not keywords |
| Web search | web-search (MCP) | DuckDuckGo/Bing/Exa |
| Full web page | web-fetch (MCP) | Playwright-based, handles JS |
| GitHub README | web-search (MCP) | `fetchGithubReadme` |
| GitHub operations | `gh` CLI | Authenticated, `--json` + `--jq` |
| Past work / decisions | mem-search (MCP) | `search` → `timeline` → `get_observations` |

### ⛔ Web Search/Fetch

**NEVER use built-in `WebFetch` or `WebSearch` — blocked by hook.** Use MCP alternatives via `ToolSearch`:

| Need | ToolSearch query |
|------|-----------------|
| Web search | `+web-search search` |
| GitHub README | `+web-search fetch` |
| Fetch page | `+web-fetch fetch` |
