---
sidebar_position: 3
title: /prd
description: Generate Product Requirements Documents (PRDs) with optional research through strategic conversation before /spec
---

# /prd

Generate Product Requirements Documents (PRDs) through strategic conversation with optional research. Use `/prd` before `/spec` when requirements are unclear or you need to explore trade-offs before committing to a technical plan.

```bash
$ pilot
> /prd "Add real-time notifications for team updates"
> /prd "We need better onboarding — users drop off after signup"
> /prd "Build an API for third-party integrations"
```

## When to Use

| Situation | Command |
|-----------|---------|
| Idea is vague, requirements unclear | `/prd` first, then `/spec` |
| Need to explore trade-offs and alternatives | `/prd` |
| Want research on competitors or prior art | `/prd` with Standard or Deep research |
| Requirements are well-defined | `/spec` directly |
| Small task, no planning needed | Quick mode (just chat) |

## Workflow

```
Understand → Research (optional) → Clarify → Propose → Converge → Write PRD → Hand off to /spec
```

The entire flow is conversational — one question at a time, no rushing to solutions.

### 1. Understand the Idea

Restates your idea, explores project context, and identifies the core problem. Doesn't jump to solutions.

### 2. Research (Optional)

Choose a research tier at the start:

| Tier | What It Does | Best For |
|------|-------------|----------|
| **Quick** | Skip research, go straight to brainstorming | Simple ideas, well-understood domains |
| **Standard** | Web search for competitors, prior art, best practices (5-10 queries) | Most features — quick context gathering |
| **Deep** | Parallel research agents covering multiple angles simultaneously | Complex domains, market research, technical exploration |

Research findings are embedded in the PRD under a dedicated section.

### 3. Ask Clarifying Questions

One question at a time. Focuses on purpose, users, constraints, success criteria, and scope boundaries. Challenges assumptions and surfaces trade-offs. Typically 3-6 questions.

### 4. Propose Approaches

Proposes 2-3 implementation approaches with clear trade-offs. Leads with a recommendation and explains why. Gets your choice before proceeding.

### 5. Converge on Scope

States what's in scope, what's explicitly out, identifies core user flows step-by-step, and notes technical context for `/spec`.

### 6. Write PRD

Saves a PRD to `docs/prd/YYYY-MM-DD-<slug>.md` with structured metadata and these sections:

| Section | Purpose |
|---------|---------|
| **Problem Statement** | What problem, for whom, why now — the north star |
| **Core User Flows** | Step-by-step from the user's perspective |
| **Scope** | In scope / explicitly out of scope with reasoning |
| **Technical Context** | Lightweight notes for the implementer — constraints, integration points |
| **Key Decisions** | Trade-offs made during the conversation with reasoning |
| **Research Findings** | Embedded research results (when research tier was Standard or Deep) |

### 7. Hand Off to /spec

After you confirm the PRD, asks whether to hand off to `/spec` immediately or save for later. If yes, `/spec` is invoked automatically with a reference to the PRD.

## PRD Output

PRDs are saved to `docs/prd/` — separate from implementation plans in `docs/plans/`. This keeps requirements documents (the "what" and "why") distinct from technical specs (the "how").

Each PRD includes structured metadata: Created date, Author, Category, Status (Draft/Final), and Research tier used.

PRDs are visible in the **Pilot Console** under the **Requirements** tab, where you can browse, annotate, share, and archive them — the same experience as the Specifications tab.

## Comparison with /spec

| Aspect | /prd | /spec |
|--------|------|-------|
| **Purpose** | Explore and define requirements | Plan and implement |
| **Output** | PRD (what and why) | Implementation plan + code (how) |
| **Style** | Conversational, strategic | Structured, technical |
| **Research** | Optional (Quick/Standard/Deep) | No research phase |
| **Questions** | One at a time, exploratory | Batched, focused on design |
| **When** | Idea stage, unclear requirements | Ready to build |
| **Duration** | 5-15 minutes of conversation | Hours of automated work |
