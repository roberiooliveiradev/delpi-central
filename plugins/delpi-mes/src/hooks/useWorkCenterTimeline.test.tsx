import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { getWorkCenterTimeline } from "../api/mesApi";
import { useWorkCenterTimeline } from "./useWorkCenterTimeline";

vi.mock("../api/mesApi", () => ({ getWorkCenterTimeline: vi.fn() }));

const timeline = { branch: "01", workCenter: "CT-35", from: "f", to: "t", referenceAt: "r", items: [] };

beforeEach(() => vi.clearAllMocks());

describe("useWorkCenterTimeline", () => {
  it("does not request history without permission or selected work center", () => {
    renderHook(() => useWorkCenterTimeline("01", "CT-35", "sig", false));
    renderHook(() => useWorkCenterTimeline("01", null, "sig", true));
    expect(getWorkCenterTimeline).not.toHaveBeenCalled();
  });

  it("requests exactly the selected work center for the local day", async () => {
    vi.mocked(getWorkCenterTimeline).mockResolvedValue(timeline);
    const hook = renderHook(() => useWorkCenterTimeline("01", "CT-35", "sig", true));
    await waitFor(() => expect(hook.result.current.data).toEqual(timeline));
    expect(getWorkCenterTimeline).toHaveBeenCalledTimes(1);
    expect(getWorkCenterTimeline).toHaveBeenCalledWith("01", "CT-35", expect.any(String), expect.any(AbortSignal));
  });

  it("isolates errors and retries on demand", async () => {
    vi.mocked(getWorkCenterTimeline).mockRejectedValueOnce(new Error("histórico indisponível")).mockResolvedValue(timeline);
    const hook = renderHook(() => useWorkCenterTimeline("01", "CT-35", "sig", true));
    await waitFor(() => expect(hook.result.current.error).toBe("histórico indisponível"));
    hook.result.current.retry();
    await waitFor(() => expect(hook.result.current.data).toEqual(timeline));
    expect(getWorkCenterTimeline).toHaveBeenCalledTimes(2);
  });

  it("aborts the previous request when the selected work center changes", async () => {
    const signals: AbortSignal[] = [];
    vi.mocked(getWorkCenterTimeline).mockImplementation((_b, _w, _f, signal) => { signals.push(signal!); return new Promise(() => {}); });
    const hook = renderHook(({ center }) => useWorkCenterTimeline("01", center, "sig", true), { initialProps: { center: "CT-35" } });
    await waitFor(() => expect(signals).toHaveLength(1));
    hook.rerender({ center: "CT-41" });
    await waitFor(() => expect(signals).toHaveLength(2));
    expect(signals[0].aborted).toBe(true);
    expect(getWorkCenterTimeline).toHaveBeenLastCalledWith("01", "CT-41", expect.any(String), expect.any(AbortSignal));
  });

  it("refetches when the selected run signature changes", async () => {
    vi.mocked(getWorkCenterTimeline).mockResolvedValue(timeline);
    const hook = renderHook(({ signature }) => useWorkCenterTimeline("01", "CT-35", signature, true), { initialProps: { signature: "a" } });
    await waitFor(() => expect(hook.result.current.data).toEqual(timeline));
    hook.rerender({ signature: "b" });
    await waitFor(() => expect(getWorkCenterTimeline).toHaveBeenCalledTimes(2));
  });
});
