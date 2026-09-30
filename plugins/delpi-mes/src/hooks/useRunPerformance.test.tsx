import { renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getRunPerformance } from "../api/mesApi";
import { useRunPerformance } from "./useRunPerformance";

vi.mock("../api/mesApi", () => ({ getRunPerformance: vi.fn() }));
const payload = {
  runId: "run-1", branch: "01", workCenter: "CT-35", status: "running",
  referenceAt: "2026-01-01T10:00:00Z",
  performance: { idealCycleSeconds: 1.8, producedPieces: 10, producingSeconds: 60, performancePercent: 90, actualAverageCycleSeconds: 2, actualThroughputPerHour: 600, expectedThroughputPerHour: 700, dataQuality: "complete", idealProductionSeconds: 18 },
};

describe("useRunPerformance", () => {
  afterEach(() => vi.clearAllMocks());

  it("fetches once per selected run", async () => {
    vi.mocked(getRunPerformance).mockResolvedValue(payload);
    const hook = renderHook(() => useRunPerformance("run-1"));
    await waitFor(() => expect(hook.result.current.data).not.toBeNull());
    expect(getRunPerformance).toHaveBeenCalledTimes(1);
    expect(vi.mocked(getRunPerformance).mock.calls[0][0]).toBe("run-1");
  });
  it("refetches only when the run changes or refreshKey advances", async () => {
    vi.mocked(getRunPerformance).mockResolvedValue(payload);
    const hook = renderHook(({ runId, refKey }) => useRunPerformance(runId, refKey), { initialProps: { runId: "run-1", refKey: "t1" } });
    await waitFor(() => expect(getRunPerformance).toHaveBeenCalledTimes(1));
    hook.rerender({ runId: "run-1", refKey: "t1" });
    expect(getRunPerformance).toHaveBeenCalledTimes(1);
    hook.rerender({ runId: "run-1", refKey: "t2" });
    await waitFor(() => expect(getRunPerformance).toHaveBeenCalledTimes(2));
    hook.rerender({ runId: "run-2", refKey: "t2" });
    await waitFor(() => expect(getRunPerformance).toHaveBeenCalledTimes(3));
    expect(vi.mocked(getRunPerformance).mock.calls[2][0]).toBe("run-2");
  });
  it("keeps prior data while a refresh is in flight", async () => {
    vi.mocked(getRunPerformance).mockResolvedValue(payload);
    const hook = renderHook(({ refKey }) => useRunPerformance("run-1", refKey), { initialProps: { refKey: "t1" } });
    await waitFor(() => expect(hook.result.current.data).not.toBeNull());
    vi.mocked(getRunPerformance).mockReturnValue(new Promise(() => undefined));
    hook.rerender({ refKey: "t2" });
    expect(hook.result.current.data).toEqual(payload);
  });
  it("surfaces errors locally and supports retry", async () => {
    vi.mocked(getRunPerformance).mockRejectedValue(new Error("indisponível"));
    const hook = renderHook(() => useRunPerformance("run-1"));
    await waitFor(() => expect(hook.result.current.error).toBe("indisponível"));
    vi.mocked(getRunPerformance).mockResolvedValue(payload);
    hook.result.current.retry();
    await waitFor(() => expect(hook.result.current.data).not.toBeNull());
    expect(hook.result.current.error).toBeNull();
  });
  it("does nothing without a run id and aborts on unmount", async () => {
    let signal: AbortSignal | undefined;
    vi.mocked(getRunPerformance).mockImplementation((_id, requestSignal) => { signal = requestSignal; return new Promise(() => undefined); });
    const idle = renderHook(() => useRunPerformance(null));
    expect(getRunPerformance).not.toHaveBeenCalled();
    idle.unmount();
    const hook = renderHook(() => useRunPerformance("run-1"));
    await waitFor(() => expect(signal).toBeDefined());
    hook.unmount();
    expect(signal?.aborted).toBe(true);
  });
});
