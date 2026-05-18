---
sidebar_position: 3
title: Security Scanner
description: Built-in credential scanner — catches secrets in prompts, file reads, Bash commands, command output, and staged commits before they reach Claude's context or git history. 24 patterns ported from gitleaks and TruffleHog.
---

# Security Scanner

Built-in credential scanner that catches secrets before they leak — into Claude's context **or** into git history.

The scanner ships as a single hook (`credential_scanner.py`) registered on four events. It runs entirely on your machine, fail-closed by default. Nothing is uploaded.

## What gets scanned

| Event | What is scanned | What happens on a match |
|-------|-----------------|-------------------------|
| `UserPromptSubmit` | The prompt text you typed | Blocks delivery to Claude; exit 2 with a stderr message |
| `PreToolUse(Read)` | The file's basename **and** content (binary-safe, BOM-aware) — symlinks resolved before the name check | Denies the read |
| `PreToolUse(Bash)` | Command text, `$VAR` / `${VAR}` env values, `cat` / `head` / `tail` file targets, `git commit` staged diff + staged blobs, chained `git add … && git commit` files | Denies the Bash call |
| `PostToolUse(Bash)` | Combined `stdout + stderr` (first 1 MB) | Drops the tool result so Claude sees the block reason instead of the secret-containing output |

## What gets detected

**24 secret patterns** ported from [gitleaks](https://github.com/gitleaks/gitleaks) and [TruffleHog](https://github.com/trufflesecurity/trufflehog), grouped by category:

| Category | Rules |
|----------|-------|
| Cloud | `aws-access-key`, `gcp-api-key`, `private-key` (PEM/SSH) |
| Source control | `github-pat`, `github-fine-grained`, `gitlab-pat` |
| Package registry | `npm-token` |
| Communication | `slack-token`, `slack-webhook`, `discord-webhook`, `telegram-bot-token`, `twilio-sid` |
| Email | `sendgrid-key`, `mailgun-key`, `mailchimp-key` |
| Payment | `stripe-secret-key`, `stripe-restricted-key` |
| AI | `openai-key`, `openai-project-key`, `anthropic-key` |
| Auth | `jwt` |
| Generic | `generic-secret`, `env-assignment`, `connection-string` |

Generic patterns apply a Shannon-entropy filter (3.0–3.5 bits/char) so obvious test values like `API_KEY=test12345` don't trip the scanner.

## `.env` files are name-blocked unconditionally

Any file whose basename is `.env` or starts with `.env.` (e.g. `.env.local`, `.env.production`) is denied at `PreToolUse(Read)` **regardless of content**. Symlinks are resolved before the name check — `safe.txt → /tmp/.env` is blocked too.

The agent doesn't need to read raw secrets to understand the schema. If it needs to know which keys exist, it should ask you to list them.

## Allow tags (one-shot bypass)

Add a tag to your **next user prompt** to bypass the scan for the current turn:

| Tag | Effect |
|-----|--------|
| `[allow-secret]` | Allow secret findings to pass through |
| `[allow-all]` | Bypass all scanner checks |

**One-shot semantics.** The tag is honoured for the *first* tool call after the prompt. Subsequent tool calls in the same turn are re-blocked unless you re-tag in a new prompt. Tags in assistant messages or inside the Bash command string are NOT honoured (prompt-injection defense).

The block message always quotes the exact tag to use and a sample retry phrasing.

## Toggle

The scanner is **ON by default**. Toggle it from the Console:

```
Console (localhost:41777)  →  Settings  →  Security  →  Credential Scanner
```

The setting persists to `~/.pilot/config.json` (`securityScanner.credentialScanner`). The launcher exports `PILOT_CREDENTIAL_SCANNER_ENABLED` based on this value; restart Pilot after toggling.

:::warning Fail-closed by default
Disabling the scanner skips all four scan entry points. Only turn it off if you have an explicit reason and accept that secrets may enter the transcript or a commit.
:::

## Why two attack surfaces

Credential leaks via AI agents come in two flavours, and the scanner closes both with a single hook:

- **Context leak.** A secret read into the session ends up in transcripts, summaries, mem-search indexes, and every tool call the agent makes afterwards. Scrubbing context after the fact is unreliable.
- **Commit leak.** A secret committed to git, even briefly, must be treated as compromised. Mirrors are everywhere; rotation is the only fix.

The four entry points (prompt, file read, Bash command, Bash output) cover the realistic paths a secret takes to enter context. The `git commit` staged-diff scan closes the commit-time path.

## What's not covered (yet)

- **PII detection** (emails, SSN, phones, credit cards, IPs) — not in the pattern set.
- **`Grep` / `Glob` output** — covered indirectly via the Read scan on the underlying file content.
- **`Edit` / `Write` / `MultiEdit` pre-flight scanning** — once Claude has the secret in context, blocking the write doesn't unleak it.
- **Subagent and MCP tool outputs** — out of scope for v1.

## See also

- [Hooks Pipeline](./hooks.md) — where the scanner registers
- [Pilot Console](./console.md) — Settings → Security toggle
