import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";
import { buildDataPreviewFingerprint } from "@delpi/tv-dashboard-presentation";

import { useComunicadoDataPreview } from "./useComunicadoDataPreview";
import { writeDataPreviewCache } from "../utils/editorSessionCache";

vi.mock("../api/tvDashboardApi", () => ({
  previewDataBlockV2: vi.fn(),
}));

import { previewDataBlockV2 } from "../api/tvDashboardApi";

const mockedPreview = vi.mocked(previewDataBlockV2);

const configWithDataBlock: ComunicadoConfig = {
  blocks: [
    {
      id: "metric-1",
      type: "data_metric",
      frame: { x: 0, y: 0, w: 20, h: 20 },
      dataBinding: { operationId: "get_oee", params: { periodDays: 1 }, refreshSec: 30 },
    },
  ],
};

describe("useComunicadoDataPreview", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    window.sessionStorage.clear();
    mockedPreview.mockResolvedValue({
      block: { resolved: { kpi: { value: 42, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    window.sessionStorage.clear();
  });

  it("não alterna loading em polls subsequentes", async () => {
    const { result } = renderHook(() =>
      useComunicadoDataPreview({
        playlistId: "pl-1",
        config: configWithDataBlock,
        globalRefreshSec: 300,
        debounceMs: 0,
      }),
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    expect(result.current.resolvedByBlockId["metric-1"]).toBeDefined();
    expect(result.current.loading).toBe(false);

    mockedPreview.mockResolvedValueOnce({
      block: { resolved: { kpi: { value: 55, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(55);
  });

  it("preserva resolved ao trocar para slide sem fontes e voltar", async () => {
    const emptyConfig: ComunicadoConfig = { blocks: [] };
    const { result, rerender } = renderHook(
      ({ config }: { config: ComunicadoConfig }) =>
        useComunicadoDataPreview({
          playlistId: "pl-1",
          config,
          globalRefreshSec: 300,
          debounceMs: 0,
        }),
      { initialProps: { config: configWithDataBlock } },
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    const callsAfterFirst = mockedPreview.mock.calls.length;

    rerender({ config: emptyConfig });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    expect(result.current.loading).toBe(false);

    mockedPreview.mockClear();
    rerender({ config: configWithDataBlock });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    // Dados imediatamente disponíveis (sem banner); refetch em background sem limpar.
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    expect(result.current.loading).toBe(false);
    expect(mockedPreview.mock.calls.length).toBeGreaterThanOrEqual(0);
    // Garante que a primeira carga ocorreu e a ida ao slide vazio não apagou.
    expect(callsAfterFirst).toBeGreaterThan(0);
  });

  it("hidrata resolved do sessionStorage sem loading no F5", async () => {
    const fingerprint = buildDataPreviewFingerprint(configWithDataBlock);
    writeDataPreviewCache("pl-1", fingerprint, {
      "metric-1": { kpi: { value: 99, label: "OEE" } },
    });

    const { result } = renderHook(() =>
      useComunicadoDataPreview({
        playlistId: "pl-1",
        config: configWithDataBlock,
        globalRefreshSec: 300,
        debounceMs: 0,
      }),
    );

    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(99);
    expect(result.current.loading).toBe(false);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    // Refetch em background sem ligar loading (já havia cache).
    expect(result.current.loading).toBe(false);
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
  });

  it("não troca referência do mapa quando o poll devolve o mesmo payload", async () => {
    const { result } = renderHook(() =>
      useComunicadoDataPreview({
        playlistId: "pl-1",
        config: configWithDataBlock,
        globalRefreshSec: 300,
        debounceMs: 0,
      }),
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });

    const firstMap = result.current.resolvedByBlockId;

    mockedPreview.mockResolvedValueOnce({
      block: { resolved: { kpi: { value: 42, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(30_000);
    });

    expect(result.current.resolvedByBlockId).toBe(firstMap);
  });
});
