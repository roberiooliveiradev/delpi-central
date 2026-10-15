/**
 * NDJSON progressive transport client tests (doc 70 §16):
 * incremental parsing, UTF-8 chunk boundaries, sequence/dedup,
 * malformed-line handling, terminal requirement, turn_error, and
 * the automatic legacy-JSON fallback on the same request.
 */
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DeliaInteractionError,
  submitInteractionTurn,
} from "./interactionClient";
import type { DeliaActivityEvent } from "./interactionClient";

const RESULT_PAYLOAD = {
  session_id: "s-1",
  user_turn_id: "ut-1",
  result_turn_id: "rt-1",
  content: "Resposta da DÉLIA.",
  epistemic_class: "OBSERVATION",
  limitations: [],
  generated_at: "2026-01-01T00:00:00+00:00",
  model_invocation_id: null,
  grounding_status: "GROUNDED",
  provenance: null,
  confirmation_request: null,
  presentation: { version: "1" },
};

function event(overrides: Record<string, unknown> = {}) {
  return {
    type: "activity_event",
    version: "1",
    event_id: `ev-${Math.random()}`,
    sequence: 1,
    timestamp: "2026-01-01T00:00:00+00:00",
    session_id: "s-1",
    turn_id: "ut-1",
    phase: "REQUEST_RECEIVED",
    state: "completed",
    label_code: "REQUEST_RECEIVED",
    ...overrides,
  };
}

function ndjsonResponse(lines: string[], options?: { chunks?: number }) {
  const body = lines.join("\n") + "\n";
  const encoder = new TextEncoder();
  const bytes = encoder.encode(body);
  const split = options?.chunks ?? 3;
  const size = Math.max(1, Math.ceil(bytes.length / split));
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (let i = 0; i < bytes.length; i += size) {
        controller.enqueue(bytes.slice(i, i + size));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "application/x-ndjson" },
  });
}

function token() {
  return "host-token";
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("NDJSON progressive transport", () => {
  it("streams events incrementally then returns the terminal result", async () => {
    const lines = [
      JSON.stringify(event({ sequence: 1 })),
      JSON.stringify(
        event({ sequence: 2, phase: "CONTEXTUALIZING", state: "running" }),
      ),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    const result = await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events.map((e) => e.phase)).toEqual([
      "REQUEST_RECEIVED",
      "CONTEXTUALIZING",
    ]);
    expect(result.content).toBe("Resposta da DÉLIA.");
    expect(result.grounding_status).toBe("GROUNDED");
    // presentation.v1 payload survived the stream unchanged.
    expect(result.presentation).not.toBeNull();
  });

  it("sends the opt-in Accept header", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        ndjsonResponse([
          JSON.stringify({
            type: "turn_result",
            version: "1",
            result: RESULT_PAYLOAD,
          }),
        ]),
      );
    vi.stubGlobal("fetch", fetchMock);
    await submitInteractionTurn("oi", { getAccessToken: token });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(String((init.headers as Record<string, string>).Accept)).toContain(
      "application/x-ndjson",
    );
  });

  it("parses records split across arbitrary UTF-8 chunk boundaries", async () => {
    const lines = [
      JSON.stringify(
        event({
          sequence: 1,
          owner_ref: { display_name: "DAVI — Dados e Informações" },
        }),
      ),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(ndjsonResponse(lines, { chunks: 97 })),
    );
    const events: DeliaActivityEvent[] = [];
    const result = await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events).toHaveLength(1);
    expect(events[0].owner_ref?.display_name).toContain("DAVI");
    expect(result.result_turn_id).toBe("rt-1");
  });

  it("drops duplicate and out-of-order sequences", async () => {
    const lines = [
      JSON.stringify(event({ sequence: 1 })),
      JSON.stringify(event({ sequence: 2, phase: "CONTEXTUALIZING" })),
      JSON.stringify(event({ sequence: 2, phase: "FAILED" })),
      JSON.stringify(event({ sequence: 1, phase: "CANCELLED" })),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events.map((e) => e.sequence)).toEqual([1, 2]);
  });

  it("drops the same event_id delivered twice", async () => {
    const dup = event({ sequence: 1 });
    const lines = [
      JSON.stringify(dup),
      JSON.stringify({ ...dup, sequence: 3 }),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events).toHaveLength(1);
  });

  it("skips malformed non-terminal lines but still needs the terminal", async () => {
    const lines = [
      "{not-json",
      JSON.stringify(event({ sequence: 1 })),
      "garbage{{{",
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    const result = await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events).toHaveLength(1);
    expect(result.session_id).toBe("s-1");
  });

  it("fails closed when the stream ends without a terminal record", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        ndjsonResponse([JSON.stringify(event({ sequence: 1 }))]),
      ),
    );
    await expect(
      submitInteractionTurn("oi", { getAccessToken: token }),
    ).rejects.toMatchObject({ code: "invalid_response" });
  });

  it("turn_error becomes a DeliaInteractionError, never a success", async () => {
    const lines = [
      JSON.stringify(event({ sequence: 1 })),
      JSON.stringify(event({ sequence: 2, phase: "FAILED", state: "failed" })),
      JSON.stringify({
        type: "turn_error",
        version: "1",
        code: "model_timeout",
        message: "timeout",
      }),
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() =>
        Promise.resolve(ndjsonResponse(lines)),
      ),
    );
    const events: DeliaActivityEvent[] = [];
    await expect(
      submitInteractionTurn("oi", {
        getAccessToken: token,
        onActivityEvent: (e) => events.push(e),
      }),
    ).rejects.toBeInstanceOf(DeliaInteractionError);
    await expect(
      submitInteractionTurn("oi", {
        getAccessToken: token,
        onActivityEvent: (e) => events.push(e),
      }),
    ).rejects.toMatchObject({ code: "model_timeout" });
    expect(events.map((e) => e.phase)).toContain("FAILED");
  });

  it("rejects events with unknown phases or bad shapes", async () => {
    const lines = [
      JSON.stringify(event({ sequence: 1, phase: "INVENTED_PHASE" })),
      JSON.stringify({ type: "activity_event", version: "1", sequence: "x" }),
      JSON.stringify(event({ sequence: 2, phase: "CONTEXTUALIZING" })),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events.map((e) => e.sequence)).toEqual([2]);
  });

  it("allowlists ref fields — hostile keys never reach the callback", async () => {
    const lines = [
      JSON.stringify(
        event({
          sequence: 1,
          capability_ref: {
            remote_name: "list_items",
            arguments: { secret: "ACCESS-SECRET" },
            binding: { token: "tok" },
          },
        }),
      ),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    const wire = JSON.stringify(events);
    expect(wire).not.toContain("ACCESS-SECRET");
    expect(wire).not.toContain("binding");
    expect(events[0].capability_ref?.remote_name).toBe("list_items");
  });

  it("bounds the number of delivered events", async () => {
    const lines = [
      ...Array.from({ length: 80 }, (_, i) =>
        JSON.stringify(event({ sequence: i + 1 })),
      ),
      JSON.stringify({
        type: "turn_result",
        version: "1",
        result: RESULT_PAYLOAD,
      }),
    ];
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ndjsonResponse(lines)));
    const events: DeliaActivityEvent[] = [];
    const result = await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events.length).toBeLessThanOrEqual(64);
    expect(result.session_id).toBe("s-1");
  });

  it("falls back to the legacy JSON body on the same request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(RESULT_PAYLOAD), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    const events: DeliaActivityEvent[] = [];
    const result = await submitInteractionTurn("oi", {
      getAccessToken: token,
      onActivityEvent: (e) => events.push(e),
    });
    expect(events).toHaveLength(0);
    expect(result.content).toBe("Resposta da DÉLIA.");
  });

  it("never re-sends the request after a stream error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        ndjsonResponse([JSON.stringify(event({ sequence: 1 }))]),
      );
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      submitInteractionTurn("oi", { getAccessToken: token }),
    ).rejects.toBeInstanceOf(DeliaInteractionError);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
