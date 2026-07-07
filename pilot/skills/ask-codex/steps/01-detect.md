## Step 1: Detect Codex (MANDATORY — before any recipe)

This skill requires the OpenAI Codex CLI. Users without Codex get friendly guidance, never errors.

### 1.1 Resolve CODEX_BIN

Check the same locations as the Pilot installer (maintainer note: path list replicated from `installer/platform_utils.py:is_codex_installed`, and overlapping `launcher/updater.py:_find_codex_binary` — update the copies together):

```bash
CODEX_BIN=$(command -v codex 2>/dev/null)
case "$CODEX_BIN" in
  /*) ;;              # absolute path: a real executable
  *) CODEX_BIN="" ;;  # empty, or a shell function/alias name (e.g. a codex() wrapper) - not launchable by scripts
esac
if [ -z "$CODEX_BIN" ]; then
  for p in "$HOME/.codex/bin/codex" "$HOME/.local/bin/codex" "/usr/local/bin/codex"; do
    [ -f "$p" ] && [ -x "$p" ] && CODEX_BIN="$p" && break
  done
fi
if [ -z "$CODEX_BIN" ]; then echo "CODEX_MISSING"; else echo "CODEX_BIN=$CODEX_BIN"; "$CODEX_BIN" --version; fi
```

The `case` guard matters: `command -v` also matches shell functions and aliases (Pilot itself wraps `codex` in a function), which the bundled scripts' `Popen` cannot launch — only an absolute path or a real PATH fallback counts.

**If `CODEX_MISSING`** → STOP the skill with this message (no recipe execution, no error/traceback):

> ℹ️ `/ask-codex` needs the OpenAI Codex CLI, which isn't installed on this system. Install it (see https://developers.openai.com/codex/cli, e.g. `npm install -g @openai/codex`), authenticate with `codex login`, then re-invoke `/ask-codex`. Everything else in Pilot Shell works without Codex.

**If resolved:** use `"$CODEX_BIN"` in every recipe (never bare `codex`), and export it in the environment when launching the bundled scripts — they read it and default to `codex` otherwise:

```bash
export CODEX_BIN
```

### 1.2 Auth caveat — do not trust `codex login status`

`codex login status` can false-positive: observed reporting "Logged in using ChatGPT" while every real call failed with 401 "refresh token was revoked". Do NOT pre-gate on it. Instead, when any recipe fails with an auth error (401, "refresh token was revoked", "Please log out and sign in again"):

1. Tell the user to run `codex logout && codex login` — it is interactive, so suggest typing `! codex login` in the prompt to run it in-session.
2. STOP retrying until the user confirms re-login — repeated launches cannot fix revoked auth.
