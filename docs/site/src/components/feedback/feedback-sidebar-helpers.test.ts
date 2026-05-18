/**
 * Pure conditional logic for the FeedbackSidebar's Submit button label and
 * post-submit success state. Split out so the renderer remains untestable
 * without a DOM/RTL stack while the user-visible copy is still under tests.
 */
import { describe, expect, test } from "vitest";
import {
  submitButtonLabel,
  submitButtonDisabled,
  successStateText,
} from "./feedback-sidebar-helpers";
import type { Decision } from "@/lib/sharing";

const approve: Decision = { verdict: "approve" };
const requestChanges: Decision = { verdict: "request_changes" };

describe("submitButtonLabel", () => {
  test("'Submit Review' when a decision is selected, regardless of annotation count", () => {
    expect(submitButtonLabel(approve, 0)).toBe("Submit Review");
    expect(submitButtonLabel(approve, 2)).toBe("Submit Review");
    expect(submitButtonLabel(requestChanges, 5)).toBe("Submit Review");
  });

  test("'Submit N annotations' when no decision is selected", () => {
    expect(submitButtonLabel(null, 1)).toBe("Submit 1 annotation");
    expect(submitButtonLabel(null, 3)).toBe("Submit 3 annotations");
  });

  test("'Submit Feedback' when no decision AND no annotations (disabled-state label)", () => {
    expect(submitButtonLabel(null, 0)).toBe("Submit Feedback");
  });
});

describe("submitButtonDisabled", () => {
  test("enabled when at least one of (decision, annotation count > 0)", () => {
    expect(submitButtonDisabled(approve, 0)).toBe(false);
    expect(submitButtonDisabled(null, 1)).toBe(false);
    expect(submitButtonDisabled(approve, 2)).toBe(false);
  });

  test("disabled when no decision AND zero annotations", () => {
    expect(submitButtonDisabled(null, 0)).toBe(true);
  });
});

describe("successStateText", () => {
  test("approve + 0 annotations → 'Approved'", () => {
    expect(successStateText(approve, 0)).toEqual({
      title: "Approved",
      detail: "Your review was sent to the spec owner.",
    });
  });

  test("approve + N annotations → 'Approved with N annotation(s)'", () => {
    expect(successStateText(approve, 1).title).toBe("Approved with 1 annotation");
    expect(successStateText(approve, 3).title).toBe("Approved with 3 annotations");
  });

  test("request_changes + 0 annotations → 'Requested changes'", () => {
    expect(successStateText(requestChanges, 0).title).toBe("Requested changes");
  });

  test("request_changes + N annotations → 'Requested changes with N annotation(s)'", () => {
    expect(successStateText(requestChanges, 2).title).toBe(
      "Requested changes with 2 annotations",
    );
  });

  test("no decision + N annotations → 'Feedback submitted'", () => {
    expect(successStateText(null, 2)).toEqual({
      title: "Feedback submitted",
      detail: "2 annotations sent to the spec owner.",
    });
    expect(successStateText(null, 1).detail).toBe("1 annotation sent to the spec owner.");
  });
});
