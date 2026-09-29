import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getMonitoring } from "../api/mesApi";
import { MONITORING_POLL_MS } from "../constants/monitoring";
import { useMonitoringData } from "./useMonitoringData";

vi.mock("../api/mesApi", () => ({ getMonitoring: vi.fn() }));
const payload = { branch: "01", referenceAt: "2026-01-01T00:00:00Z", summary: { activeRuns: 0, producing: 0, stopped: 0, paused: 0, unclassifiedDowntimes: 0 }, items: [] };

describe("useMonitoringData", () => {
  beforeEach(() => { vi.clearAllMocks(); vi.useRealTimers(); Object.defineProperty(document, "hidden", { configurable: true, value: false }); Object.defineProperty(navigator, "onLine", { configurable: true, value: true }); });
  afterEach(() => { cleanup(); vi.useRealTimers(); });
  it("loads immediately and polls once per cycle without card fan-out", async () => {
    vi.useFakeTimers(); vi.mocked(getMonitoring).mockResolvedValue(payload);
    renderHook(() => useMonitoringData("01"));
    await act(async () => { await Promise.resolve(); });
    expect(getMonitoring).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(MONITORING_POLL_MS); });
    expect(getMonitoring).toHaveBeenCalledTimes(2);
  });
  it("keeps stale data when a refresh fails", async () => {
    vi.mocked(getMonitoring).mockResolvedValueOnce(payload).mockRejectedValueOnce(new Error("indisponível"));
    const hook = renderHook(() => useMonitoringData("01"));
    await waitFor(() => expect(hook.result.current.data).not.toBeNull());
    await act(async () => { await hook.result.current.refresh(); });
    expect(hook.result.current.data).toEqual(payload);
    expect(hook.result.current.error).toBe("indisponível");
  });
  it("pauses hidden/offline and resumes on visible/online", async () => {
    vi.mocked(getMonitoring).mockResolvedValue(payload);
    renderHook(() => useMonitoringData("01"));
    await waitFor(() => expect(getMonitoring).toHaveBeenCalledTimes(1));
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    document.dispatchEvent(new Event("visibilitychange"));
    expect(getMonitoring).toHaveBeenCalledTimes(1);
    Object.defineProperty(document, "hidden", { configurable: true, value: false });
    document.dispatchEvent(new Event("visibilitychange"));
    await waitFor(() => expect(getMonitoring).toHaveBeenCalledTimes(2));
    Object.defineProperty(navigator, "onLine", { configurable: true, value: false });
    window.dispatchEvent(new Event("online"));
    expect(getMonitoring).toHaveBeenCalledTimes(2);
    Object.defineProperty(navigator, "onLine", { configurable: true, value: true });
    window.dispatchEvent(new Event("online"));
    await waitFor(() => expect(getMonitoring).toHaveBeenCalledTimes(3));
  });
  it("aborts the active request on unmount", async () => {
    let signal: AbortSignal | undefined;
    vi.mocked(getMonitoring).mockImplementation((_branch, requestSignal) => { signal = requestSignal; return new Promise(() => undefined); });
    const hook = renderHook(() => useMonitoringData("01"));
    await waitFor(() => expect(signal).toBeDefined());
    hook.unmount();
    expect(signal?.aborted).toBe(true);
  });
});
