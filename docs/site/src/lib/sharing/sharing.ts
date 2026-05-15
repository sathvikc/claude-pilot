/**
 * High-level URL generation and parsing for spec sharing.
 *
 * Two URL families coexist:
 *
 *   1. Short URL (current): https://pilot-shell.com/s/<8-char-id>
 *      Payload POSTed to /api/share and stored on Upstash Redis for ≤ 7 days;
 *      anyone with the link can fetch and view.
 *
 *   2. Legacy fragment URL (back-compat only): https://pilot-shell.com/shared#<compressed-data>
 *      Compressed payload embedded in the URL fragment; never transmitted to the server.
 *      Still decoded by `Shared.tsx` so in-flight legacy links keep working.
 *
 * Teammate feedback flows back via `submitFeedback` → POST /api/share/feedback,
 * which appends to the existing share's server-side feedback queue. The old
 * "generate a feedback URL to copy back" flow is removed.
 *
 * No encryption — both formats rely on the unguessable URL itself as the access token.
 */

import { compress, decompress } from "./compress";
import type { SharePayload, FeedbackPayload } from "./types";

/** ~32KB limit — safe for all major browsers */
const MAX_INLINE_BYTES = 32_768;

export interface WebShareUrlResult {
  url: string;
}

/** Compress and build a URL. Returns null if too large or on error. */
async function buildCompressedUrl(
  payload: unknown,
  baseUrl: string,
): Promise<WebShareUrlResult | null> {
  try {
    const compressed = await compress(JSON.stringify(payload));

    if (compressed.length > MAX_INLINE_BYTES) {
      return null;
    }

    const url = `${baseUrl}#${compressed}`;
    return { url };
  } catch {
    return null;
  }
}

/** Generate a web share URL. Returns null if payload would exceed inline URL limits. */
export function generateWebShareUrl(
  payload: SharePayload,
  baseUrl: string,
): Promise<WebShareUrlResult | null> {
  return buildCompressedUrl(payload, baseUrl);
}

const SUBMIT_TIMEOUT_MS = 10_000;

export type SubmitFeedbackResult =
  | { ok: true; position: number }
  | { ok: false; reason: "not_found" | "rate_limited" | "too_large" | "network" };

/**
 * Submit a teammate's feedback batch to an existing share id. Replaces the
 * old `generateShortFeedbackUrl` flow — no copy-URL round trip; the Console's
 * poller picks the entry up directly.
 */
export async function submitFeedback(
  shareId: string,
  payload: FeedbackPayload,
  apiBaseUrl: string = "",
): Promise<SubmitFeedbackResult> {
  let res: Response;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), SUBMIT_TIMEOUT_MS);
  try {
    res = await fetch(`${apiBaseUrl}/api/share/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: shareId, payload }),
      signal: controller.signal,
    });
  } catch {
    return { ok: false, reason: "network" };
  } finally {
    clearTimeout(timeoutId);
  }
  if (res.status === 404) return { ok: false, reason: "not_found" };
  if (res.status === 413) return { ok: false, reason: "too_large" };
  if (res.status === 429) return { ok: false, reason: "rate_limited" };
  if (!res.ok) return { ok: false, reason: "network" };
  try {
    const body = (await res.json()) as { ok?: boolean; position?: number };
    if (body.ok !== true || typeof body.position !== "number") {
      return { ok: false, reason: "network" };
    }
    return { ok: true, position: body.position };
  } catch {
    return { ok: false, reason: "network" };
  }
}

/**
 * Parse hash fragment from any supported URL format:
 *   - Website: pilot-shell.com/shared#<data>
 *   - Console shared: localhost/#/shared/<data>
 *   - Console feedback: localhost/#/feedback/<data>
 *   - Raw hash: #<data>
 *
 * Returns null if no data could be extracted.
 */
export function parseHashFragment(input: string): { data: string } | null {
  const hashIdx = input.indexOf("#");
  if (hashIdx === -1) return null;

  const fragment = input.slice(hashIdx + 1);
  // Strip any legacy ?key= params
  const qIdx = fragment.indexOf("?");
  const path = qIdx === -1 ? fragment : fragment.slice(0, qIdx);

  // Strip known Console path prefixes
  let data = path;
  if (data.startsWith("/shared/")) data = data.slice("/shared/".length);
  else if (data.startsWith("/feedback/")) data = data.slice("/feedback/".length);

  if (!data) return null;
  return { data };
}

/**
 * Decompress a share payload.
 * Returns null on any failure.
 */
export async function decompressSharePayload(
  data: string,
): Promise<SharePayload | null> {
  if (!data) return null;
  try {
    return JSON.parse(await decompress(data)) as SharePayload;
  } catch {
    return null;
  }
}

/**
 * Detect whether a payload is a SharePayload (has specContent).
 */
export function isSharePayload(payload: unknown): payload is SharePayload {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "specContent" in payload &&
    typeof (payload as SharePayload).specContent === "string"
  );
}

/**
 * Decompress a payload from a legacy hash fragment. Only `share`-shaped
 * payloads are supported now; legacy `feedback` URL payloads no longer exist
 * but the type stays in the return shape so the (unused) feedback branch in
 * Shared.tsx surfaces a graceful "this is a feedback URL" error.
 */
export async function decompressHashPayload(
  data: string,
): Promise<{ type: "share"; payload: SharePayload } | { type: "feedback" } | null> {
  if (!data) return null;
  try {
    const parsed = JSON.parse(await decompress(data));
    if (isSharePayload(parsed)) {
      return { type: "share", payload: parsed as SharePayload };
    }
    return { type: "feedback" };
  } catch {
    return null;
  }
}
