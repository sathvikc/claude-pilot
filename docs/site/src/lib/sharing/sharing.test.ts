import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./compress", () => ({
  compress: vi.fn(async (s: string) => `compressed:${s.length}`),
  decompress: vi.fn(async (s: string) => s),
}));

import { submitFeedback } from "./sharing";
import type { FeedbackPayload } from "./types";

const samplePayload: FeedbackPayload = {
  annotations: [
    { id: "a1", blockId: "b1", originalText: "x", text: "tiny note", createdAt: 1 },
  ],
  author: "Tester",
  planPath: "docs/plans/x.md",
  createdAt: 0,
};

const fetchMock = vi.fn();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("submitFeedback", () => {
  it("returns { ok: true, position } on 201", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true, position: 0 }), { status: 201 }),
    );
    const result = await submitFeedback("ABCDEFGH", samplePayload);
    expect(result).toEqual({ ok: true, position: 0 });
  });

  it("POSTs to /api/share/feedback with id + payload as body", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true, position: 1 }), { status: 201 }),
    );
    await submitFeedback("ABCDEFGH", samplePayload);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/share/feedback");
    const body = JSON.parse(String((init as RequestInit).body));
    expect(body.id).toBe("ABCDEFGH");
    expect(body.payload.author).toBe("Tester");
  });

  it("returns not_found on 404", async () => {
    fetchMock.mockResolvedValueOnce(new Response("", { status: 404 }));
    const result = await submitFeedback("ABCDEFGH", samplePayload);
    expect(result).toEqual({ ok: false, reason: "not_found" });
  });

  it("returns too_large on 413", async () => {
    fetchMock.mockResolvedValueOnce(new Response("", { status: 413 }));
    const result = await submitFeedback("ABCDEFGH", samplePayload);
    expect(result).toEqual({ ok: false, reason: "too_large" });
  });

  it("returns rate_limited on 429", async () => {
    fetchMock.mockResolvedValueOnce(new Response("", { status: 429 }));
    const result = await submitFeedback("ABCDEFGH", samplePayload);
    expect(result).toEqual({ ok: false, reason: "rate_limited" });
  });

  it("returns network on fetch rejection", async () => {
    fetchMock.mockRejectedValueOnce(new Error("offline"));
    const result = await submitFeedback("ABCDEFGH", samplePayload);
    expect(result).toEqual({ ok: false, reason: "network" });
  });
});
