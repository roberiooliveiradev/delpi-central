import { afterEach, describe, expect, it, vi } from "vitest";
import { getMonitoring, getWorkCenterTimeline } from "./mesApi";

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
  it("loads the daily timeline only for the selected work center", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ workCenter: "CT 35", items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getWorkCenterTimeline("01", "CT 35", "2026-01-01T03:00:00.000Z");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/work-centers/CT%2035/timeline?branch=01&from=2026-01-01T03%3A00%3A00.000Z");
  });
});
