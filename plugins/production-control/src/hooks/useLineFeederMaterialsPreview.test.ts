// @vitest-environment jsdom

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import type { LineFeederMaterialsPreviewPayload } from "../types";
import { useLineFeederMaterialsPreview } from "./useLineFeederMaterialsPreview";

const previewMock = vi.fn();

vi.mock("../api/ppcApi", () => ({
  previewLineFeederMaterials: (...args: unknown[]) => previewMock(...args),
}));

function payload(
  partial: Partial<LineFeederMaterialsPreviewPayload> = {},
): LineFeederMaterialsPreviewPayload {
  return {
    branch: "01",
    hours_per_work_center: 3,
    publication: {
      generation_id: "g1",
      publication_revision: "1",
      published_at: null,
      published_by: null,
      source_refreshed_at: null,
      start_date: null,
      end_date: null,
    },
    preview_completeness: "complete",
    operational_list_safe: true,
    stop_reasons: [],
    demand_warnings: [],
    horizon: { covered_operation_count: 2, work_centers: [] },
    summary: {
      material_count: 1,
      covered_count: 0,
      to_pick_count: 1,
      at_risk_count: 0,
      unknown_count: 0,
      to_collect_qty: 60,
    },
    materials: [
      {
        product_code: "MP-001",
        description: "Cabo",
        unit: "M",
        required_qty: 100,
        factory_available_qty: 40,
        to_collect_qty: 60,
        source_available_qty: 200,
        status: "to_pick",
        work_centers: ["CT-A"],
        origins: [],
      },
    ],
    ...partial,
  };
}

afterEach(() => {
  previewMock.mockReset();
});

describe("useLineFeederMaterialsPreview", () => {
  it("envia branch, CTs e horas para materials/preview", async () => {
    previewMock.mockResolvedValue(payload());
    const { result } = renderHook(() => useLineFeederMaterialsPreview("01"));
    await act(async () => {
      await result.current.run({
        workCenters: ["CT-A", "CT-B"],
        hoursPerWorkCenter: 3,
      });
    });
    expect(previewMock).toHaveBeenCalledWith(
      expect.objectContaining({
        branch: "01",
        workCenters: ["CT-A", "CT-B"],
        hoursPerWorkCenter: 3,
      }),
    );
    expect(result.current.data?.materials[0].to_collect_qty).toBe(60);
  });

  it("reconsulta com saldo atualizado sem reaproveitar valor anterior", async () => {
    previewMock
      .mockResolvedValueOnce(payload())
      .mockResolvedValueOnce(
        payload({
          materials: [
            {
              product_code: "MP-001",
              description: "Cabo",
              unit: "M",
              required_qty: 100,
              factory_available_qty: 75,
              to_collect_qty: 25,
              source_available_qty: 200,
              status: "to_pick",
              work_centers: ["CT-A"],
              origins: [],
            },
          ],
          summary: {
            material_count: 1,
            covered_count: 0,
            to_pick_count: 1,
            at_risk_count: 0,
            unknown_count: 0,
            to_collect_qty: 25,
          },
        }),
      );
    const { result } = renderHook(() => useLineFeederMaterialsPreview("01"));
    const query = { workCenters: ["CT-A"], hoursPerWorkCenter: 3 };
    await act(async () => {
      await result.current.run(query);
    });
    expect(result.current.data?.materials[0].to_collect_qty).toBe(60);
    await act(async () => {
      result.current.reload();
    });
    await waitFor(() =>
      expect(result.current.data?.materials[0].to_collect_qty).toBe(25),
    );
    expect(previewMock).toHaveBeenCalledTimes(2);
  });

  it("mapeia HTTP 409 como programação desatualizada", async () => {
    previewMock.mockRejectedValue(
      new HttpRequestError("stale", 409),
    );
    const { result } = renderHook(() => useLineFeederMaterialsPreview("01"));
    await act(async () => {
      await result.current.run({
        workCenters: ["CT-A"],
        hoursPerWorkCenter: 2,
      });
    });
    expect(result.current.error?.kind).toBe("stale");
    expect(result.current.data).toBeNull();
  });

  it("descarta resposta antiga ao trocar de filial", async () => {
    let resolveFirst: ((value: LineFeederMaterialsPreviewPayload) => void) | null =
      null;
    previewMock.mockImplementationOnce(
      () =>
        new Promise<LineFeederMaterialsPreviewPayload>((resolve) => {
          resolveFirst = resolve;
        }),
    );
    const { result, rerender } = renderHook(
      ({ branch }) => useLineFeederMaterialsPreview(branch),
      { initialProps: { branch: "01" as const } },
    );
    void act(() => {
      void result.current.run({
        workCenters: ["CT-A"],
        hoursPerWorkCenter: 1,
      });
    });
    rerender({ branch: "02" });
    await act(async () => {
      resolveFirst?.(payload({ branch: "01" }));
    });
    expect(result.current.data).toBeNull();
  });
});
