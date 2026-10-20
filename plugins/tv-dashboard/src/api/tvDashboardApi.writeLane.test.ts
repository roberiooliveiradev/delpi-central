import { afterEach, describe, expect, it, vi } from "vitest";

import { applyPresentationMutations, resolveWriteExpectedRevision } from "./tvDashboardApi";

function ok(data: unknown) {
  return Promise.resolve(
    new Response(JSON.stringify({ success: true, data }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

describe("tvDashboardApi — OCC write lane", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("resolveWriteExpectedRevision aceita valor, thunk e guard ausente", () => {
    expect(resolveWriteExpectedRevision({ expectedRevision: 4 })).toBe(4);
    expect(resolveWriteExpectedRevision({ expectedRevision: () => 9 })).toBe(9);
    expect(resolveWriteExpectedRevision({ expectedRevision: null })).toBeNull();
    expect(resolveWriteExpectedRevision(undefined)).toBeUndefined();
    expect(resolveWriteExpectedRevision({ clientId: "c" })).toBeUndefined();
  });

  it("serializa mutations do mesmo cliente e resolve If-Match no envio", async () => {
    // Regressão TV-ICON-CONFLICT: gestos rápidos (color picker) disparavam N
    // mutations concorrentes com o mesmo expectedRevision stale → self-409.
    const sentIfMatch: Array<string | null> = [];
    const tracker = { revision: 7 };
    let releaseFirst!: () => void;
    const firstGate = new Promise<void>((resolve) => (releaseFirst = resolve));

    const fetchMock = vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
      sentIfMatch.push(new Headers(init?.headers).get("If-Match"));
      if (sentIfMatch.length === 1) {
        return firstGate.then(() => {
          tracker.revision += 1;
          return ok({ appliedOps: ["a"], playlistRevision: tracker.revision });
        });
      }
      tracker.revision += 1;
      return ok({ appliedOps: ["x"], playlistRevision: tracker.revision });
    });
    vi.stubGlobal("fetch", fetchMock);

    const guard = () => ({ expectedRevision: () => tracker.revision });
    const p1 = applyPresentationMutations("pl-1", "s1", [{ op: "a" }], guard());
    const p2 = applyPresentationMutations("pl-1", "s1", [{ op: "b" }], guard());
    const p3 = applyPresentationMutations("pl-1", "s1", [{ op: "c" }], guard());

    await vi.waitFor(() => expect(sentIfMatch).toEqual(['"7"']));
    releaseFirst();

    await Promise.all([p1, p2, p3]);
    // cada escrita enviou a revisão pós-ack da anterior — sem self-conflict
    expect(sentIfMatch).toEqual(['"7"', '"8"', '"9"']);
  });
});
