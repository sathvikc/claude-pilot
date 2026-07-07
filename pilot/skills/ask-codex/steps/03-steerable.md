## Step 3: Steerable Sessions (app-server)

`codex exec` is fire-and-wait: once started you can only wait. The app-server (`codex app-server`, JSON-RPC 2.0 over stdio, SAME ChatGPT-subscription auth — not metered API) lets you WATCH a run and CORRECT it mid-flight. Two bundled clients, both defaulting to read-only + `approvalPolicy=never`; both read `CODEX_BIN` from the environment (default `codex`) and bound every JSON-RPC request with a deadline — a live-but-silent app-server is terminated and reported, never a silent hang. A slow `steer:`/`interrupt` acknowledgement only fails that command; it never kills the active turn.

Set the scripts dir once (the skill install location honors `CLAUDE_CONFIG_DIR`):

```bash
SKILL_SCRIPTS="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/ask-codex/scripts"
```

**INTERACTIVE (recommended for jobs >20 min)** — background session with a file control plane:

```bash
# 1. launch in the background; optional first --prompt
python3 "$SKILL_SCRIPTS/codex_session.py" \
  --dir <session-dir> --cwd <abs-repo> --model gpt-5.5 --effort xhigh [--prompt "<first turn>"]
# 2. WATCH live: tail <session-dir>/progress.log (turn start, each exec command, streamed answer, done)
# 3. DRIVE by appending one command per line to <session-dir>/control:
echo 'steer: <correction>' >> <session-dir>/control   # inject into the ACTIVE turn
echo 'turn: <new prompt>'  >> <session-dir>/control   # start another turn
echo 'interrupt'           >> <session-dir>/control   # stop the active turn
echo 'status'              >> <session-dir>/control   # dump state to status.json
echo 'quit'                >> <session-dir>/control   # shut down
# 4. read the answer from <session-dir>/result.txt
```

Pass `--sandbox workspace-write` to let Codex edit the tree. Use an absolute `--dir` under the scratchpad.

**Failure contract:** errors are never silent. A failed turn writes `[turn failed] <error>` to `result.txt` (treat that prefix as an error sentinel, not an answer) and logs `[turn FAILED: …]`; a startup failure writes `[startup failed] <error>` and logs `[startup FAILED: …]`; a failed `turn:` command logs `[turn start FAILED: …]`. On any auth error, apply the Step 1.2 re-login guidance.

**ONE-SHOT (simpler, optional pre-timed steer)** — single turn, no live control:

```bash
python3 "$SKILL_SCRIPTS/codex_appserver.py" "<prompt>" \
  --cwd <abs-repo> --model gpt-5.5 --effort xhigh -o <abs-out>.txt \
  [--steer "<text>" --steer-after <secs>] [--timeout <secs>]
```

Prefer plain `codex exec` (Step 2) for fire-and-forget; use these when you need to see and steer a run.

A benign `rmcp AuthorizationRequired` MCP-noise line may appear on stderr, same as the CLI. Protocol reference: https://developers.openai.com/codex/app-server
