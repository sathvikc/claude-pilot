---
sidebar_position: 6
title: Remote Control
description: Control Pilot Shell sessions from your phone, tablet, or any browser
---

# [Remote Control](https://youtu.be/Ko7_tC1fMMM?si=kWDzYiQvxlkZTrRK)

Control Pilot Shell sessions from your phone, tablet, or any browser.

Start a `/spec` task at your desk, then monitor and steer it from the couch. Your full local environment stays available — filesystem, MCP servers, hooks, rules, and project configuration. Nothing moves to the cloud.

## Prerequisites

[Remote Control](https://youtu.be/Ko7_tC1fMMM?si=kWDzYiQvxlkZTrRK) requires the **native install** of Claude Code, not the npm version. If you have the npm version installed, uninstall it first:

```bash
npm uninstall -g @anthropic-ai/claude-code   # Remove npm version if installed
curl -fsSL https://claude.ai/install.sh | bash  # Install native version
```

You also need a **Pro, Max, Team, or Enterprise** Claude subscription. API keys won't work with Remote Control.

## Setup

### 1. Start Pilot Shell

```bash
pilot
```

Start a Pilot Shell session as usual. This loads all hooks, rules, MCP servers, and project configuration.

### 2. Activate Remote Control

| Method | How |
| ------ | --- |
| **Single session** | Type `/remote-control` inside the Pilot Shell session |
| **All sessions** | Run `/config` in Claude Code and set "Enable Remote Control for all sessions" to `true` |

### 3. Connect from your phone

Open the **Claude Mobile App** ([iOS](https://apps.apple.com/app/claude-by-anthropic/id6473753684) / [Android](https://play.google.com/store/apps/details?id=com.anthropic.claude)) and go to the **Code** tab. Your Pilot Shell session appears there with a green status dot when online.

You can also connect from any browser at [claude.ai/code](https://claude.ai/code).

## How It Works

Sessions started via `pilot` carry over all rules, hooks, MCP servers, and project configuration. The Claude App and web interface are just a window into your local session — your machine does all the work.

- **Full Pilot Shell experience** — hooks, rules, skills, MCP servers all stay active
- **Outbound-only** — no ports open on your machine, all traffic over TLS
- **Multi-device sync** — send messages from terminal, browser, and phone interchangeably
- **Auto-reconnect** — reconnects automatically when your laptop wakes from sleep

## Keeping Your Computer Awake

Your computer must stay awake for the Remote Control connection to remain active. On macOS, use [Amphetamine](https://apps.apple.com/de/app/amphetamine/id937984704) to keep your Mac awake with the display off — this way you can walk away without the session disconnecting.

## Start Sessions via SSH From Your Phone

The above approach assumes you start sessions via `pilot` on your computer first. To also start new Pilot Shell sessions from your phone:

1. Install [Termius](https://termius.com/) on your **mobile phone** (not your computer)
2. Connect via SSH to your computer
3. Run `pilot` in any project directory

### macOS Sleep Support

Turn on **Remote Login** in macOS Settings → General → Sharing → Advanced → Remote Login. This lets you SSH into your Mac even while it's sleeping.

### Outside Your Home Network

The Claude App approach works everywhere out of the box — no extra setup needed.

For the SSH/Termius approach, you need network connectivity to your computer. Install [Tailscale](https://tailscale.com/) on both your computer and phone to create a VPN tunnel that works from anywhere.

## Use Cases

| Pattern | Description |
| ------- | ----------- |
| **Walk away** | Start a `/spec` task at your desk, monitor progress from your phone |
| **Couch review** | Queue up code reviews at your workstation, approve from the couch |
| **Quick check** | Glance at a running session from your phone without going back to your desk |
| **Multi-device** | Heavy coding from terminal, lighter interactions from browser, quick approvals from phone |

## Troubleshooting

If Remote Control doesn't connect or shows authentication errors, run `/logout` followed by `/login` inside Claude Code. This re-authenticates your session and resolves most connection issues.

## Telegram Integration

Control Pilot Shell directly from Telegram. Send messages to your bot, and Claude responds in the same chat — with full access to your local environment, hooks, rules, and MCP servers.

### Setup

1. **Install the Telegram plugin** — follow the setup instructions at [claude-plugins-official/telegram](https://github.com/anthropics/claude-plugins-official/tree/main/external_plugins/telegram). This walks you through creating a Telegram bot, connecting it to your account, and installing the plugin via `claude plugin install`.

2. **Start Pilot Shell** — run `pilot` as usual. Pilot Shell automatically detects the Telegram plugin and enables the `--channels` flag on launch. No extra configuration needed.

3. **Message your bot** — open the Telegram chat with your bot and start sending messages. Claude receives them as channel messages and responds directly in the chat.

### How It Works

On every launch, Pilot Shell runs `claude plugin list --json` to check if the `telegram@claude-plugins-official` plugin is installed and enabled. When detected, it passes `--channels plugin:telegram@claude-plugins-official` to Claude Code, which activates the Telegram channel alongside your terminal session.

This means you can interact with Claude from both your terminal and Telegram simultaneously — heavy coding from the terminal, quick checks and approvals from Telegram.

### Use Cases

| Pattern | Description |
| ------- | ----------- |
| **On-the-go approvals** | Approve `/spec` plans from Telegram while away from your desk |
| **Quick questions** | Ask Claude about your codebase from your phone without opening a terminal |
| **Progress updates** | Check on long-running tasks from anywhere |
| **Multi-device** | Terminal for coding, Telegram for monitoring and quick interactions |

## Limitations

- Your computer must stay awake (see above)
- One remote connection per Claude Code instance
- Terminal must stay open (close it and the session ends)
