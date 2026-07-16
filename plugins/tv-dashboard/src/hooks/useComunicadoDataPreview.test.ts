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

function withParams(periodDays: number): ComunicadoConfig {
  return {
    blocks: [
      {
        id: "metric-1",
        type: "data_metric",
        frame: { x: 0, y: 0, w: 20, h: 20 },
        dataBinding: { operationId: "get_oee", params: { periodDays }, refreshSec: 30 },
      },
    ],
  };
}

describe("useComunicadoDataPreview", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
    mockedPreview.mockResolvedValue({
      block: { resolved: { kpi: { value: 42, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);
  });

  afterEach(() => {
    vi.clearAllMocks();
    window.sessionStorage.clear();
  });

  it("carrega uma vez na abertura sem poll automático", async () => {
    const { result } = renderHook(() =>
      useComunicadoDataPreview({
        playlistId: "pl-1",
        config: configWithDataBlock,
      }),
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    expect(mockedPreview).toHaveBeenCalledTimes(1);

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });

    expect(mockedPreview).toHaveBeenCalledTimes(1);
    expect(result.current.loading).toBe(false);
  });

  it("mudança de fingerprint dispara refetch automático (debounce)", async () => {
    const { result, rerender } = renderHook(
      ({ config }: { config: ComunicadoConfig }) =>
        useComunicadoDataPreview({
          playlistId: "pl-1",
          config,
        }),
      { initialProps: { config: withParams(1) } },
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    mockedPreview.mockClear();
    mockedPreview.mockResolvedValue({
      block: { resolved: { kpi: { value: 77, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    rerender({ config: withParams(7) });
    await act(async () => {
      await Promise.resolve();
    });
    expect(mockedPreview).not.toHaveBeenCalled();
    expect(result.current.isDataPreviewStale).toBe(false);

    await act(async () => {
      await new Promise((r) => setTimeout(r, 450));
    });

    expect(mockedPreview).toHaveBeenCalledTimes(1);
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(77);
    expect(result.current.isDataPreviewStale).toBe(false);
  });

  it("refreshDataPreview busca de novo com forceRefresh", async () => {
    const { result, rerender } = renderHook(
      ({ config }: { config: ComunicadoConfig }) =>
        useComunicadoDataPreview({
          playlistId: "pl-1",
          config,
        }),
      { initialProps: { config: withParams(1) } },
    );

    await act(async () => {
      await Promise.resolve();
    });

    rerender({ config: withParams(7) });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 450));
    });

    mockedPreview.mockClear();
    mockedPreview.mockResolvedValueOnce({
      block: { resolved: { kpi: { value: 55, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    await act(async () => {
      await result.current.refreshDataPreview({ force: true });
    });

    expect(mockedPreview).toHaveBeenCalledTimes(1);
    expect(mockedPreview.mock.calls[0]?.[0]?.forceRefresh).toBe(true);
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(55);
    expect(result.current.isDataPreviewStale).toBe(false);
  });

  it("mover/redimensionar bloco (mesmo fingerprint de dados) não marca stale", async () => {
    const { result, rerender } = renderHook(
      ({ config }: { config: ComunicadoConfig }) =>
        useComunicadoDataPreview({
          playlistId: "pl-1",
          config,
        }),
      { initialProps: { config: configWithDataBlock } },
    );

    await act(async () => {
      await Promise.resolve();
    });
    mockedPreview.mockClear();

    const moved: ComunicadoConfig = {
      blocks: [
        {
          id: "metric-1",
          type: "data_metric",
          frame: { x: 40, y: 40, w: 30, h: 25 },
          dataBinding: { operationId: "get_oee", params: { periodDays: 1 }, refreshSec: 30 },
        },
      ],
    };
    expect(buildDataPreviewFingerprint(moved)).toBe(buildDataPreviewFingerprint(configWithDataBlock));

    rerender({ config: moved });
    await act(async () => {
      await Promise.resolve();
    });

    expect(mockedPreview).not.toHaveBeenCalled();
    expect(result.current.isDataPreviewStale).toBe(false);
  });

  it("preserva resolved ao trocar para slide sem fontes e voltar", async () => {
    const emptyConfig: ComunicadoConfig = { blocks: [] };
    const { result, rerender } = renderHook(
      ({ config }: { config: ComunicadoConfig }) =>
        useComunicadoDataPreview({
          playlistId: "pl-1",
          config,
        }),
      { initialProps: { config: configWithDataBlock } },
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);

    rerender({ config: emptyConfig });
    await act(async () => {
      await Promise.resolve();
    });
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    expect(result.current.isDataPreviewStale).toBe(false);

    mockedPreview.mockClear();
    rerender({ config: configWithDataBlock });
    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(42);
    expect(result.current.loading).toBe(false);
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
      }),
    );

    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(99);
    expect(result.current.loading).toBe(false);

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.loading).toBe(false);
    expect(mockedPreview).not.toHaveBeenCalled();
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(99);
  });
});
