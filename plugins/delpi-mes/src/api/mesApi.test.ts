import { afterEach, describe, expect, it, vi } from "vitest";
import { getDowntimeAnalytics, getDowntimeFilterOptions, getDowntimes, getMonitoring, getRunPerformance, getWorkCenterTimeline } from "./mesApi";

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
  it("loads performance once for a given run id", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ runId: "run-1", performance: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await getRunPerformance("run-1");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/runs/run-1/performance");
  });
  it("loads the daily timeline only for the selected work center", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ workCenter: "CT 35", items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getWorkCenterTimeline("01", "CT 35", { from: "2026-01-01T03:00:00.000Z" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/work-centers/CT%2035/timeline?branch=01&from=2026-01-01T03%3A00%3A00.000Z");
  });
  it("forwards the optional period end of the daily timeline", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ workCenter: "CT-35", items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getWorkCenterTimeline("01", "CT-35", { from: "2026-01-01T03:00:00.000Z", to: "2026-01-02T02:59:59.999Z" });
    expect(fetchMock.mock.calls[0][0]).toContain("to=2026-01-02T02%3A59%3A59.999Z");
  });

  it("forwards every downtime filter to the canonical read endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ items: [], total: 0, page: 1, pageSize: 50 }));
    vi.stubGlobal("fetch", fetchMock);
    await getDowntimes({
      branch: "02",
      workCenter: "CT 35",
      from: "2026-02-01T03:00:00.000Z",
      to: "2026-02-11T03:00:00.000Z",
      reasonCode: "SETUP",
      source: "system",
      classification: "pending",
      sort: "oldest",
      page: 3,
      pageSize: 100,
    });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/downtimes?");
    expect(url).toContain("branch=02");
    expect(url).toContain("page=3");
    expect(url).toContain("pageSize=100");
    expect(url).toContain("workCenter=CT+35");
    expect(url).toContain("from=2026-02-01T03%3A00%3A00.000Z");
    expect(url).toContain("to=2026-02-11T03%3A00%3A00.000Z");
    expect(url).toContain("reasonCode=SETUP");
    expect(url).toContain("source=system");
    expect(url).toContain("classification=pending");
    expect(url).toContain("sort=oldest");
  });

  it("queries a single downtime by id for the detail deep link", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ items: [], total: 0, page: 1, pageSize: 1 }));
    vi.stubGlobal("fetch", fetchMock);
    await getDowntimes({ branch: "01", downtimeId: "42", page: 1, pageSize: 1 });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("downtimeId=42");
    expect(url).toContain("branch=01");
  });

  it("forwards only metric-determining filters to the analytics endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ summary: {}, byReason: [], byWorkCenter: [], byDay: [], byWeekdayHour: [], quality: {} }));
    vi.stubGlobal("fetch", fetchMock);
    await getDowntimeAnalytics({
      branch: "01",
      from: "2026-02-01T03:00:00.000Z",
      to: "2026-02-11T03:00:00.000Z",
      workCenter: "CT 35",
      reasonCode: "SETUP",
      source: "system",
      classification: "pending",
    });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/downtimes/analytics?");
    expect(url).toContain("branch=01");
    expect(url).toContain("from=2026-02-01T03%3A00%3A00.000Z");
    expect(url).toContain("to=2026-02-11T03%3A00%3A00.000Z");
    expect(url).toContain("workCenter=CT+35");
    expect(url).toContain("reasonCode=SETUP");
    expect(url).toContain("source=system");
    expect(url).toContain("classification=pending");
    // paginação, ordenação e detalhe nunca são determinantes de métrica
    expect(url).not.toContain("page=");
    expect(url).not.toContain("sort=");
    expect(url).not.toContain("downtimeId=");
  });

  it("loads the read-only filter options scoped by branch", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response({ reasons: [], sources: [] }));
    vi.stubGlobal("fetch", fetchMock);
    await getDowntimeFilterOptions("02");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/downtimes/filter-options?branch=02");
  });
});
