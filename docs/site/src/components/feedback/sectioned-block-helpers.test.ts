/**
 * Tests for SectionedBlockRenderer helper logic.
 *
 * The remote spec viewer must render each task's `**Objective:**` description
 * inline below the task title (matching the Console SpecTaskCard UX), not as
 * a nested collapsible the reader has to click open. `extractObjectiveBlocks`
 * is the pure split point: given a task body's blocks, return the
 * Objective-labelled blocks separately from the rest so the renderer can
 * place them inline.
 */
import { describe, expect, test } from "vitest";
import { extractObjectiveBlocks, orderSections } from "./sectioned-block-helpers";
import {
  DISPLAYED_SECTIONS_ORDERED,
  IMPLEMENTATION_TASKS_HEADING,
  TASKS_HEADING_BUGFIX,
} from "@/lib/sharing/displayed-sections";
import type { Block } from "@/lib/annotation/types";

function paragraph(id: string, content: string, order: number): Block {
  return { id, type: "paragraph", content, order, startLine: order + 1 };
}

describe("extractObjectiveBlocks", () => {
  test("separates the **Objective:** paragraph from later **Files:** blocks", () => {
    const blocks: Block[] = [
      paragraph("b1", "**Objective:** Encode the bug as a failing test.", 0),
      paragraph("b2", "**Files:**", 1),
      { id: "b3", type: "list-item", content: "tests/foo.test.ts", order: 2, startLine: 3 },
    ];
    const { objective, rest } = extractObjectiveBlocks(blocks);
    expect(objective).not.toBeNull();
    expect(objective!.length).toBeGreaterThan(0);
    expect(
      objective!.some((b) => b.content.includes("Encode the bug as a failing test.")),
    ).toBe(true);
    // The Objective's own label prefix must be stripped — readers see prose,
    // not `**Objective:** Encode …`.
    expect(objective!.every((b) => !b.content.startsWith("**Objective:**"))).toBe(true);
    // `rest` keeps the non-Objective fields so the renderer can still group
    // Files / Key Decisions / DoD into their collapsibles.
    expect(rest.some((b) => b.content.includes("Files"))).toBe(true);
    expect(rest.some((b) => b.content.startsWith("**Objective:**"))).toBe(false);
  });

  test("returns null objective when no **Objective:** label is present", () => {
    const blocks: Block[] = [
      paragraph("b1", "**Files:** foo.ts", 0),
      paragraph("b2", "**Key Decisions:** none", 1),
    ];
    const { objective, rest } = extractObjectiveBlocks(blocks);
    expect(objective).toBeNull();
    expect(rest).toHaveLength(2);
  });

  test("Objective paragraph spanning a multi-line content stays whole", () => {
    const blocks: Block[] = [
      paragraph(
        "b1",
        "**Objective:** First sentence.\nSecond sentence on the next line.",
        0,
      ),
      paragraph("b2", "**Files:** bar.ts", 1),
    ];
    const { objective, rest } = extractObjectiveBlocks(blocks);
    expect(objective).not.toBeNull();
    const joined = objective!.map((b) => b.content).join("\n");
    expect(joined).toContain("First sentence.");
    expect(joined).toContain("Second sentence on the next line.");
    expect(rest.some((b) => b.content.includes("Files"))).toBe(true);
  });
});

describe("orderSections", () => {
  const TASKS_HEADINGS = [IMPLEMENTATION_TASKS_HEADING, TASKS_HEADING_BUGFIX] as const;

  test("preserves canonical order when input already matches", () => {
    const input = [
      { heading: "Summary" },
      { heading: "Approach" },
      { heading: "Goal Verification" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual([
      "Summary",
      "Approach",
      "Goal Verification",
    ]);
  });

  test("reorders sections into canonical order when input is reversed", () => {
    const input = [
      { heading: "Deferred Ideas" },
      { heading: "Open Questions" },
      { heading: "E2E Test Scenarios" },
      { heading: "Goal Verification" },
      { heading: "Risks and Mitigations" },
      { heading: "Assumptions" },
      { heading: "Runtime Environment" },
      { heading: "Context for Implementer" },
      { heading: "Approach" },
      { heading: "Out of Scope" },
      { heading: "Summary" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual([
      "Summary",
      "Out of Scope",
      "Approach",
      "Context for Implementer",
      "Runtime Environment",
      "Assumptions",
      "Risks and Mitigations",
      "Goal Verification",
      "E2E Test Scenarios",
      "Open Questions",
      "Deferred Ideas",
    ]);
  });

  test("drops Progress Tracking and File Structure sections silently", () => {
    const input = [
      { heading: "Summary" },
      { heading: "Progress Tracking" },
      { heading: "File Structure" },
      { heading: "Approach" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual(["Summary", "Approach"]);
  });

  test("positions Implementation Tasks last regardless of source position", () => {
    const input = [
      { heading: "Summary" },
      { heading: "Implementation Tasks" },
      { heading: "Approach" },
      { heading: "Deferred Ideas" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual([
      "Summary",
      "Approach",
      "Deferred Ideas",
      "Implementation Tasks",
    ]);
  });

  test("positions bugfix Tasks heading last too", () => {
    const input = [
      { heading: "Summary" },
      { heading: "Tasks" },
      { heading: "Investigation" },
      { heading: "Behavior Contract" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual([
      "Summary",
      "Investigation",
      "Behavior Contract",
      "Tasks",
    ]);
  });

  test("preamble sections (empty heading) always come first, in their original order", () => {
    const input = [
      { heading: "Approach" },
      { heading: "" },
      { heading: "Summary" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual(["", "Summary", "Approach"]);
  });

  test("drops unknown headings silently", () => {
    const input = [
      { heading: "Summary" },
      { heading: "Acme Internal Notes" },
      { heading: "Approach" },
    ];
    const out = orderSections(input, DISPLAYED_SECTIONS_ORDERED, TASKS_HEADINGS);
    expect(out.map((s) => s.heading)).toEqual(["Summary", "Approach"]);
  });
});
