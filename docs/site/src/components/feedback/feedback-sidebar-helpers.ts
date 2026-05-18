/**
 * Pure conditional logic for the FeedbackSidebar's Submit button and
 * post-submit success state. Kept separate from the renderer so the
 * user-visible copy is unit-testable without a DOM/RTL stack.
 */
import type { Decision } from "@/lib/sharing";

function plural(n: number, singular: string, plural?: string): string {
  return `${n} ${n === 1 ? singular : (plural ?? `${singular}s`)}`;
}

/** Button label that adapts to whether a verdict is selected and how many inline annotations exist. */
export function submitButtonLabel(decision: Decision | null, annotationCount: number): string {
  if (decision) return "Submit Review";
  if (annotationCount > 0) return `Submit ${plural(annotationCount, "annotation")}`;
  return "Submit Feedback";
}

/** Submit is enabled iff EITHER a decision is selected OR there is ≥ 1 annotation. */
export function submitButtonDisabled(decision: Decision | null, annotationCount: number): boolean {
  return decision === null && annotationCount === 0;
}

/** Post-submit success state copy. Branches on decision verdict + annotation count. */
export function successStateText(
  decision: Decision | null,
  submittedCount: number,
): { title: string; detail: string } {
  if (decision) {
    const verb = decision.verdict === "approve" ? "Approved" : "Requested changes";
    const tail = submittedCount > 0 ? ` with ${plural(submittedCount, "annotation")}` : "";
    return {
      title: `${verb}${tail}`,
      detail: "Your review was sent to the spec owner.",
    };
  }
  return {
    title: "Feedback submitted",
    detail: `${plural(submittedCount, "annotation")} sent to the spec owner.`,
  };
}
