import { afterEach, describe, expect, it, vi } from "vitest";
import { getMonitoring, getRunTimeline } from "./mesApi";

afterEach(() => vi.unstubAllGlobals());
const response = (data: unknown) => new Response(JSON.stringify({ success: true, message: "OK", data }), { status: 200 });

describe("MES API", () => {
  it.each(["01", "02"] as const)("calls one monitoring endpoint for branch %s", async (branch) => {
    const fetchMock = vi.fn().mockResolvedValue(response({ branch, referenceAt: "2026-01-01T00:00:00Z", summary: {}, items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getMonitoring(branch);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain(`/monitoring?branch=${branch}`);
  });
  it("loads only the selected run timeline", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ runId: "run 1", items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getRunTimeline("run 1");
    expect(fetchMock.mock.calls[0][0]).toContain("/runs/run%201/timeline");
  });
});
