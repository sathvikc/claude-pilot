## Pilot MCP Servers

MCP tools are lazy-loaded via `ToolSearch`. Discover by keyword, then call directly. Full param schemas are returned by `ToolSearch` itself — these summaries cover purpose and minimum usage.

```
ToolSearch(query="keyword")               # Discover and load tools by keyword
ToolSearch(query="+server keyword")       # Require a specific server prefix
ToolSearch(query="select:full_tool_name") # Load a specific tool by exact name
```

All servers use the `mcp__plugin_pilot_` prefix. Tools are callable immediately after ToolSearch returns them.

---

### CodeGraph — Code Knowledge Graph (PRIMARY)

**Structural code search.** First action on any task. Replaces Grep/Glob for symbol/call/impact queries. Complements Probe (intent search — see `cli-tools.md`).

| Tool | Purpose |
|------|---------|
| `codegraph_context(task=...)` | **START HERE** — entry points + related symbols |
| `codegraph_explore(query="SymA SymB file.ts")` | Full source from all relevant files in ONE call (replaces dozens of Read/Grep calls). Use specific symbol/file names — NOT natural language. Run `codegraph_search` first to discover names. |
| `codegraph_search` | Find symbols by name |
| `codegraph_callers` / `codegraph_callees` | Trace call flow before modifying. Supplement with Grep as a *completeness check* for indirect/dynamic callers. |
| `codegraph_impact` | Blast radius before committing to a change |
| `codegraph_node` | Details + source for one symbol |
| `codegraph_files` | Project file tree (NOT Glob/ls) |

**⛔ NEVER pass `projectPath` for the current project.** The server defaults correctly. Passing it triggers a different code path that fails if `.codegraph/` isn't at that exact path. Only use it for genuinely different codebases.

```
codegraph_context(task="refactor authentication flow")
codegraph_callers(symbol="processOrder")
codegraph_impact(symbol="processOrder", depth=2)
```

---

### mem-search — Persistent Memory

Past work, decisions, context across sessions. **3-step workflow — never skip to step 3:**

1. `search(query, limit, type, project, dateStart, dateEnd)` → returns index with IDs
2. `timeline(anchor=ID or query, depth_before, depth_after)` → context around an anchor
3. `get_observations(ids=[...])` → full details for filtered IDs only

`save_memory(text, title?, project?)` to record findings.

**Types:** `bugfix`, `feature`, `refactor`, `discovery`, `decision`, `change`.

---

### context7 — Library Documentation

Up-to-date docs and code examples for any library/framework. Two steps:

1. `resolve-library-id(libraryName, query)` → returns `libraryId` like `/pypi/pytest`
2. `query-docs(libraryId, query)` → answers using indexed docs

Use descriptive queries. Max 3 calls per question per tool.

---

### web-search — Web Search

`search(query, limit?, engines?)` — DuckDuckGo / Bing / Exa, no API keys.

Article fetchers: `fetchGithubReadme(url)`, `fetchLinuxDoArticle(url)`, `fetchCsdnArticle(url)`, `fetchJuejinArticle(url)`.

---

### web-fetch — Web Page Fetching

Playwright-backed; no truncation; handles JS-rendered pages.

- `fetch_url(url, ...)` — single page
- `fetch_urls(urls=[...], ...)` — multiple pages
- `browser_install(withDeps?, force?)` — install Chromium

Useful options: `waitUntil` (`load`/`domcontentloaded`/`networkidle`), `returnHtml`, `waitForNavigation` (anti-bot).

---

### grep-mcp — GitHub Code Search

`searchGitHub(query, language?, repo?, path?, useRegexp?, matchCase?)` — finds real-world code in 1M+ public repos. Query is a literal pattern (or regex with `useRegexp=true`; prefix `(?s)` for multiline). Filter `language=["Python"]`, `repo="vercel/next-auth"`, `path="src/components/"`.

---

### Tool Selection Quick Reference

| Need | Tool |
|------|------|
| Task orientation (FIRST on every task) | `codegraph_context` |
| Symbol search / call tracing / impact | CodeGraph (`search` / `callers` / `callees` / `impact`) |
| Deep code understanding (multiple files) | `codegraph_explore` |
| Codebase search by intent | Probe CLI (see `cli-tools.md`) |
| Past work / decisions | mem-search 3-step |
| Library/framework docs | context7 |
| Web search | web-search |
| GitHub README | web-search `fetchGithubReadme` |
| Production code examples | grep-mcp |
| Full web page content | web-fetch |
