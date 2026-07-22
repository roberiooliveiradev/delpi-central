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

  it("carrega e concatena a próxima página sob demanda", async () => {
    const pagedConfig: ComunicadoConfig = {
      blocks: [{
        id: "source-1",
        type: "data_source",
        frame: { x: 0, y: 0, w: 20, h: 20 },
        dataBinding: { operationId: "list_items", params: {} },
      }],
    };
    mockedPreview
      .mockResolvedValueOnce({
        block: { resolved: {
          data: { page: 1, page_size: 30, total_pages: 2 },
          table: { rows: [{ id: 1 }], columns: [{ key: "id", label: "ID" }] },
        } },
      } as Awaited<ReturnType<typeof previewDataBlockV2>>)
      .mockResolvedValueOnce({
        block: { resolved: {
          data: { page: 2, page_size: 30, total_pages: 2 },
          table: { rows: [{ id: 2 }], columns: [{ key: "id", label: "ID" }] },
        } },
      } as Awaited<ReturnType<typeof previewDataBlockV2>>);
    const { result } = renderHook(() =>
      useComunicadoDataPreview({ playlistId: "pl-1", config: pagedConfig }),
    );
    await act(async () => { await Promise.resolve(); });
    await act(async () => { await result.current.loadMoreDataPreview("source-1"); });
    expect(result.current.resolvedByBlockId["source-1"]?.table?.rows).toEqual([
      { id: 1 },
      { id: 2 },
    ]);
    expect(mockedPreview.mock.calls[1]?.[0].block).toMatchObject({
      dataBinding: { params: { page: 2, page_size: 30 } },
    });
  });

  it("expõe loadingProgressPercent conforme blocos concluem", async () => {
    const twoBlocks: ComunicadoConfig = {
      blocks: [
        {
          id: "metric-1",
          type: "data_metric",
          frame: { x: 0, y: 0, w: 20, h: 20 },
          dataBinding: { operationId: "get_oee", params: { periodDays: 1 }, refreshSec: 30 },
        },
        {
          id: "metric-2",
          type: "data_metric",
          frame: { x: 20, y: 0, w: 20, h: 20 },
          dataBinding: { operationId: "get_otd", params: { periodDays: 1 }, refreshSec: 30 },
        },
      ],
    };

    let resolveA!: (value: Awaited<ReturnType<typeof previewDataBlockV2>>) => void;
    let resolveB!: (value: Awaited<ReturnType<typeof previewDataBlockV2>>) => void;
    const promiseA = new Promise<Awaited<ReturnType<typeof previewDataBlockV2>>>((r) => {
      resolveA = r;
    });
    const promiseB = new Promise<Awaited<ReturnType<typeof previewDataBlockV2>>>((r) => {
      resolveB = r;
    });

    mockedPreview.mockImplementation((payload) => {
      const id = (payload.block as { id?: string }).id;
      return id === "metric-1" ? promiseA : promiseB;
    });

    const { result } = renderHook(() =>
      useComunicadoDataPreview({ playlistId: "pl-progress", config: twoBlocks }),
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.loadingProgressPercent).toBe(0);

    await act(async () => {
      resolveA({
        block: { resolved: { kpi: { value: 1, label: "A" } } },
      } as Awaited<ReturnType<typeof previewDataBlockV2>>);
      await Promise.resolve();
    });

    expect(result.current.loadingProgressPercent).toBe(50);

    await act(async () => {
      resolveB({
        block: { resolved: { kpi: { value: 2, label: "B" } } },
      } as Awaited<ReturnType<typeof previewDataBlockV2>>);
      await Promise.resolve();
    });

    expect(result.current.loadingProgressPercent).toBeNull();
    expect(result.current.resolvedByBlockId["metric-1"]?.kpi?.value).toBe(1);
    expect(result.current.resolvedByBlockId["metric-2"]?.kpi?.value).toBe(2);
  });

  it("propaga erro soft do resolved para error do hook e mantém o card", async () => {
    mockedPreview.mockResolvedValue({
      block: {
        resolved: {
          error: "[403] Filial não autorizada.",
          detail: "Filial não autorizada.",
          kpi: { value: 0, label: "PPM" },
        },
      },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    const { result } = renderHook(() =>
      useComunicadoDataPreview({
        playlistId: "pl-soft-err",
        config: configWithDataBlock,
      }),
    );

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(result.current.error).toBe("[403] Filial não autorizada.");
    expect(result.current.resolvedByBlockId["metric-1"]?.error).toBe(
      "[403] Filial não autorizada.",
    );
  });

  it("falha HTTP por bloco grava resolved.error sem derrubar os demais", async () => {
    const twoBlocks: ComunicadoConfig = {
      blocks: [
        {
          id: "metric-1",
          type: "data_metric",
          frame: { x: 0, y: 0, w: 20, h: 20 },
          dataBinding: { operationId: "get_oee", params: { periodDays: 1 }, refreshSec: 30 },
        },
        {
          id: "metric-2",
          type: "data_metric",
          frame: { x: 20, y: 0, w: 20, h: 20 },
          dataBinding: { operationId: "get_otd", params: { periodDays: 1 }, refreshSec: 30 },
        },
      ],
    };

    mockedPreview.mockImplementation(async (payload) => {
      const id = (payload.block as { id?: string }).id;
      if (id === "metric-1") {
        throw new Error("Unauthorized");
      }
      return {
        block: { resolved: { kpi: { value: 88, label: "OK" } } },
      } as Awaited<ReturnType<typeof previewDataBlockV2>>;
    });

    const { result } = renderHook(() =>
      useComunicadoDataPreview({ playlistId: "pl-partial", config: twoBlocks }),
    );

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(result.current.resolvedByBlockId["metric-1"]?.error).toBe("Unauthorized");
    expect(result.current.resolvedByBlockId["metric-2"]?.kpi?.value).toBe(88);
    expect(result.current.error).toBe("Unauthorized");
  });
});
