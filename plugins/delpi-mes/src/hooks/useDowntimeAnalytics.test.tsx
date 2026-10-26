import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDowntimeAnalytics } from "../api/mesApi";
import type {
  DowntimeAnalyticsQuery,
  DowntimeAnalyticsResponse,
} from "../types/mes";
import { useDowntimeAnalytics } from "./useDowntimeAnalytics";

vi.mock("../api/mesApi", () => ({
  getDowntimeAnalytics: vi.fn(),
}));

const analyticsOf = (tag: string): DowntimeAnalyticsResponse => ({
  branch: tag,
  from: "2026-02-09T03:00:00.000Z",
  to: "2026-02-10T03:00:00.000Z",
  referenceAt: "2026-02-10T12:00:00.000Z",
  timezone: "America/Sao_Paulo",
  appliedFilters: {
    workCenter: null, reasonCode: null, source: null, classification: null,
  },
  summary: {
    totalStoppedSeconds: 3600, attributedSeconds: 3600,
    occurrencesCount: 1, averageOccurrenceSeconds: 3600,
    pendingCount: 0, openCount: 0,
  },
  byReason: [],
  byWorkCenter: [{ workCenter: "CT-" + tag, seconds: 3600, occurrencesCount: 1, averageSeconds: 3600, percentOfTotal: 100 }],
  byDay: [],
  byWeekdayHour: [],
  quality: { overlapDetected: false, overlapSeconds: 0, partial: false, factsCapped: false },
});

const query = (branch: "01" | "02"): DowntimeAnalyticsQuery => ({
  branch,
  from: "2026-02-09T03:00:00.000Z",
});

type Deferred = {
  resolve: (value: DowntimeAnalyticsResponse) => void;
  reject: (reason: unknown) => void;
  signal: AbortSignal;
};

function deferredQueue() {
  const calls: Deferred[] = [];
  vi.mocked(getDowntimeAnalytics).mockImplementation(
    (_q: unknown, signal?: AbortSignal) => {
      let resolve!: (v: DowntimeAnalyticsResponse) => void;
      let reject!: (r: unknown) => void;
      const promise = new Promise<DowntimeAnalyticsResponse>((res, rej) => {
        resolve = res;
        reject = rej;
      });
      calls.push({ resolve, reject, signal: signal ?? new AbortController().signal });
      return promise;
    },
  );
  return calls;
}

beforeEach(() => vi.clearAllMocks());

describe("useDowntimeAnalytics — isolamento por identidade de consulta", () => {
  it("nunca expõe indicadores da filial anterior, nem por um render", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ q }: { q: DowntimeAnalyticsQuery | null }) => useDowntimeAnalytics(q),
      { initialProps: { q: query("01") as DowntimeAnalyticsQuery | null } },
    );
    calls[0].resolve(analyticsOf("01"));
    await waitFor(() =>
      expect(result.current.data?.byWorkCenter[0]?.workCenter).toBe("CT-01"),
    );

    rerender({ q: query("02") });
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(calls[0].signal.aborted).toBe(true);

    calls[0].resolve(analyticsOf("STALE"));
    calls[1].resolve(analyticsOf("02"));
    await waitFor(() =>
      expect(result.current.data?.byWorkCenter[0]?.workCenter).toBe("CT-02"),
    );
  });

  it("não consulta quando a consulta é nula e recupera ao definir", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ q }: { q: DowntimeAnalyticsQuery | null }) => useDowntimeAnalytics(q),
      { initialProps: { q: null as DowntimeAnalyticsQuery | null } },
    );
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(calls.length).toBe(0);

    rerender({ q: query("01") });
    await waitFor(() => expect(calls.length).toBe(1));
    calls[0].resolve(analyticsOf("01"));
    await waitFor(() => expect(result.current.data?.branch).toBe("01"));
  });

  it("preserva o último snapshot da mesma consulta quando o refresh falha", async () => {
    const calls = deferredQueue();
    const { result } = renderHook(() => useDowntimeAnalytics(query("01")));
    calls[0].resolve(analyticsOf("01"));
    await waitFor(() => expect(result.current.data?.branch).toBe("01"));

    void result.current.refresh();
    await waitFor(() => expect(calls.length).toBe(2));
    calls[1].reject(new Error("falha de rede"));
    await waitFor(() => expect(result.current.error).toBe("falha de rede"));
    expect(result.current.data?.branch).toBe("01");
  });

  it("descarta resposta obsoleta em alternância rápida 01 ↔ 02", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ q }: { q: DowntimeAnalyticsQuery | null }) => useDowntimeAnalytics(q),
      { initialProps: { q: query("01") as DowntimeAnalyticsQuery | null } },
    );
    rerender({ q: query("02") });
    rerender({ q: query("01") });
    expect(calls.length).toBe(3);
    calls[0].resolve(analyticsOf("STALE-A"));
    calls[1].resolve(analyticsOf("STALE-B"));
    calls[2].resolve(analyticsOf("FINAL"));
    await waitFor(() => expect(result.current.data?.branch).toBe("FINAL"));
  });
});
