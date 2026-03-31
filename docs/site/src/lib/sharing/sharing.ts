/**
 * High-level URL generation and parsing for spec sharing.
 *
 * Website URL format: https://pilot-shell.com/shared#<compressed-data>
 * Console URL formats (for paste-input parsing):
 *   - https://localhost:PORT/#/shared/<data>
 *   - https://localhost:PORT/#/feedback/<data>
 *
 * All data lives in the hash fragment, which the HTTP spec guarantees
 * is never sent to the server. No encryption — data is compressed only
 * for shorter URLs (~25% shorter than the previous encrypted format).
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

/** Generate a web feedback URL. Returns null if payload would exceed inline URL limits. */
export function generateWebFeedbackUrl(
  payload: FeedbackPayload,
  baseUrl: string,
): Promise<WebShareUrlResult | null> {
  return buildCompressedUrl(payload, baseUrl);
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
 * Decompress a feedback payload.
 * Returns null on any failure.
 */
export async function decompressFeedbackPayload(
  data: string,
): Promise<FeedbackPayload | null> {
  if (!data) return null;
  try {
    return JSON.parse(await decompress(data)) as FeedbackPayload;
  } catch {
    return null;
  }
}

/**
 * Detect whether a payload is a SharePayload (has specContent)
 * vs a FeedbackPayload (has only annotations + author).
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
 * Decompress any payload from a hash fragment, auto-detecting type.
 */
export async function decompressHashPayload(
  data: string,
): Promise<{ type: "share"; payload: SharePayload } | { type: "feedback"; payload: FeedbackPayload } | null> {
  if (!data) return null;
  try {
    const parsed = JSON.parse(await decompress(data));
    if (isSharePayload(parsed)) {
      return { type: "share", payload: parsed as SharePayload };
    }
    return { type: "feedback", payload: parsed as FeedbackPayload };
  } catch {
    return null;
  }
}
