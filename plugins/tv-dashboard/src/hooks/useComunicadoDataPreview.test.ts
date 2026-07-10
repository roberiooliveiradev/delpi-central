import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { useComunicadoDataPreview } from "./useComunicadoDataPreview";

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
    mockedPreview.mockResolvedValue({
      block: { resolved: { kpi: { value: 42, label: "OEE" } } },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
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
});
