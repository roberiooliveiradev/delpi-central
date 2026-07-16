import { describe, expect, it, vi } from "vitest";

vi.mock("../api/tvDashboardApi", () => ({
  previewDataBlockV2: vi.fn(),
}));

import { previewDataBlockV2 } from "../api/tvDashboardApi";
import { previewTvDataRoute } from "./previewTvDataRoute";

const mockedPreview = vi.mocked(previewDataBlockV2);

describe("previewTvDataRoute", () => {
  it("chama preview-block com params do bloco e modo tabela para playbook", async () => {
    mockedPreview.mockResolvedValue({
      block: {
        resolved: {
          table: {
            rows: [{ op: "1" }],
            columns: [{ key: "op", label: "OP" }],
          },
        },
      },
    } as Awaited<ReturnType<typeof previewDataBlockV2>>);

    const payload = await previewTvDataRoute({
      route: {
        operationId: "list_eficiencia_fabril_appointments",
        label: "Eficiência fabril — apontamentos",
        category: "production",
        metaShape: "playbook_report",
        allowedDisplayModes: ["table", "kpi", "auto"],
      },
      block: {
        id: "src-1",
        type: "data_source",
        frame: { x: 0, y: 0, w: 10, h: 10 },
        dataBinding: {
          operationId: "list_eficiencia_fabril_appointments",
          displayMode: "auto",
          params: { dateRangePreset: "this_month", only_ok: false },
          label: "Eficiência fabril — apontamentos (carga bulk)",
        },
      },
      config: { version: 4, blocks: [] },
      playlistId: "pl-1",
    });

    expect(mockedPreview).toHaveBeenCalled();
    const body = mockedPreview.mock.calls[0]?.[0];
    expect(body?.forceRefresh).toBe(true);
    expect(body?.playlistId).toBe("pl-1");
    const binding = (body?.block as { dataBinding?: { displayMode?: string; params?: Record<string, unknown> } })
      ?.dataBinding;
    expect(binding?.displayMode).toBe("table");
    expect(binding?.params?.dateRangePreset).toBe("this_month");
    expect(binding?.params?.only_ok).toBe(false);
    expect(payload.kind).toBe("table");
    expect(payload.error).toBeUndefined();
  });
});
