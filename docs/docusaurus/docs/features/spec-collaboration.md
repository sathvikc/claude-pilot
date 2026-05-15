---
sidebar_position: 1
title: Spec Collaboration
description: Share specs and requirements with teammates from inside the Console. Their annotations flow back automatically, grouped by author. No installs on the reviewer side.
---

# Spec Collaboration

**Catch flaws in the spec, not in the PR.** Pilot Shell ships first-class collaborative review for the artefact that decides what gets built: the spec or requirement document. Reviewers don't need Pilot installed. The Console picks up their feedback automatically.

A "flaw" here is anything you'd flag in PR review — wrong approach, missed edge case, unclear scope, weak architecture, ambiguous acceptance criteria. Spot it while a one-sentence annotation is the entire fix, instead of after the agent has spent a thousand tokens implementing the wrong thing.

## Why review specs collaboratively?

Traditional code review happens *after* the agent has implemented the feature. By then, miscommunication about scope, approach, or behavior is already encoded into code that needs rewriting. Spec review moves the conversation earlier:

- **Cheapest iteration.** Changing a sentence in a spec is faster than changing a 200-line PR.
- **More reviewers, less friction.** A single share link can go to as many teammates as you want — no per-reviewer setup, no Pilot install for the reviewers.
- **Agent reads the feedback.** The annotations your team adds end up in the spec's `.annotations` file, which the agent reads at every review checkpoint inside the `/spec` workflow. Your team's intent gets baked into the implementation.

## How to share

1. Open the spec or requirement in the Console's **Specifications** or **Requirements** tab.
2. In the header card, click **Share with Teammates**.
3. The button is replaced by a persistent link of the form `https://pilot-shell.com/s/<id>`. Copy it.
4. Send the link to anyone — Slack, email, GitHub comment, wherever.

That's it. The link is permanent for the spec — you'll never need to regenerate it, even if you reload the Console or close it.

```
┌─ Spec header card ─────────────────────────────────────────────┐
│                                                                │
│  ... spec metadata ...                                         │
│                                                                │
│  Status: PENDING     [ https://pilot-shell.com/s/Ab12Cd34 ]    │
│                      [ Copy ] [ 4d left ]                      │
└────────────────────────────────────────────────────────────────┘
```

A small badge next to the link counts down the remaining lifetime. Each link is valid for 7 days from creation. After that, click **Share with Teammates** again to mint a fresh one.

## How teammates review

The link opens the spec in any modern browser — no install, no account.

1. They read the spec.
2. They put their name in the sidebar (whatever they want to be called).
3. They click the `+` button next to any block to add an annotation.
4. They click **Submit Feedback** when done.

They can submit multiple times — each submit produces a separate notification in your Console. They don't see what other reviewers wrote; feedback flows one-way, from them to you.

## What you see in the Console

Within about a minute of any teammate clicking Submit:

1. **Bell notification.** The notification bell in the Console top-right shows `"<author> left N annotations on <spec>"`. Click it to jump to the spec.
2. **Author-grouped annotation panel.** The annotation panel on the right side of the spec shows:
   - **Your annotations** at the top (the ones you added directly).
   - **From `<author>` (N)** sections below, one per reviewer, collapsible. The freshest reviewer is open by default; older ones are collapsed.
3. **Per-annotation control.** Each teammate annotation has a delete button. Keep what's useful, delete what isn't. Deletions stick — they won't reappear on the next poll cycle.

The agent reads the merged list (yours + teammates') at the next review checkpoint inside the `/spec` workflow. Author labels are preserved, so you can weight feedback by who said it if you'd like.

## Privacy and lifetime

- **No accounts.** The unguessable share link is the access token. Don't send it to people you wouldn't share the spec with.
- **7-day TTL.** Both the spec snapshot and the feedback queue expire after 7 days.
- **One-way visibility.** Teammates see the spec and add their own annotations. They cannot see annotations from you or other teammates.
- **Stored locally too.** Once feedback lands, it lives in your project's `.annotations/<spec>.json` and travels with the spec.

## See also

- The [`/spec` workflow](../workflows/spec.md) — where the agent reads annotations at its review checkpoints.
- The [`/prd` workflow](../workflows/prd.md) — same collaboration model, applied to requirements before they become specs.
- The [Console feature page](console.md) — overview of every view in the Console.
