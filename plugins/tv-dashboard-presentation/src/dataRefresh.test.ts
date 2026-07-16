import { describe, expect, it } from "vitest";

import {
  buildDataPreviewFingerprint,
  resolveDataBlockRefreshSec,
  resolvePreviewRefreshSourceIds,
  resolveStaleSourceIdsForPreviewChange,
} from "./dataRefresh";
import type { ComunicadoConfig } from "./comunicadoTypes";

describe("resolveDataBlockRefreshSec", () => {
  it("usa override do bloco quando válido", () => {
    expect(resolveDataBlockRefreshSec({ refreshSec: 120 }, 300)).toBe(120);
  });

  it("cai no globalRefreshSec quando bloco não define override", () => {
    expect(resolveDataBlockRefreshSec({}, 60)).toBe(60);
    expect(resolveDataBlockRefreshSec(undefined, 45)).toBe(45);
  });

  it("ignora override inválido e usa global ou default", () => {
    expect(resolveDataBlockRefreshSec({ refreshSec: 5 }, 90)).toBe(90);
    expect(resolveDataBlockRefreshSec({ refreshSec: 99999 }, null)).toBe(300);
  });
});

describe("buildDataPreviewFingerprint", () => {
  const baseConfig: ComunicadoConfig = {
    blocks: [
      {
        id: "b1",
        type: "data_metric",
        frame: { x: 0, y: 0, w: 20, h: 20 },
        dataBinding: { operationId: "get_oee", params: { periodDays: 1 } },
      },
    ],
  };

  it("muda quando binding ou filtros mudam", () => {
    const before = buildDataPreviewFingerprint(baseConfig);
    const after = buildDataPreviewFingerprint({
      ...baseConfig,
      blocks: [
        {
          ...baseConfig.blocks![0],
          dataBinding: { operationId: "get_oee", params: { periodDays: 7 } },
        },
      ],
    });
    expect(before).not.toBe(after);
  });

  it("não muda quando só posição do bloco muda", () => {
    const before = buildDataPreviewFingerprint(baseConfig);
    const after = buildDataPreviewFingerprint({
      ...baseConfig,
      blocks: [
        {
          ...baseConfig.blocks![0],
          frame: { x: 10, y: 10, w: 30, h: 30 },
        },
      ],
    });
    expect(before).toBe(after);
  });

  it("muda quando selectedValueFields muda", () => {
    const before = buildDataPreviewFingerprint(baseConfig);
    const after = buildDataPreviewFingerprint({
      ...baseConfig,
      blocks: [
        {
          ...baseConfig.blocks![0],
          type: "data_metric",
          dataBinding: {
            operationId: "get_oee",
            params: { periodDays: 1 },
            selectedValueFields: ["value"],
          },
        },
      ],
    });
    expect(after).not.toBe(before);
  });

  it("não muda quando só iconName do filtro muda", () => {
    const withInput: ComunicadoConfig = {
      blocks: [
        ...(baseConfig.blocks ?? []),
        {
          id: "input-1",
          type: "input",
          frame: { x: 0, y: 0, w: 20, h: 10 },
          input: {
            paramKey: "branch",
            defaultValue: "01",
            targetScope: "slide",
          },
        },
      ],
    };
    const before = buildDataPreviewFingerprint(withInput);
    const after = buildDataPreviewFingerprint({
      ...withInput,
      blocks: [
        withInput.blocks![0],
        {
          ...withInput.blocks![1],
          type: "input",
          input: {
            paramKey: "branch",
            defaultValue: "01",
            targetScope: "slide",
            iconName: "Building2",
          },
        },
      ],
    });
    expect(after).toBe(before);
  });
});

describe("resolvePreviewRefreshSourceIds", () => {
  const all = ["src-a", "src-b"];

  it("binding de uma fonte mudou → só essa fonte", () => {
    const prev = buildDataPreviewFingerprint({
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: { a: 1 } },
        },
        {
          id: "src-b",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: { a: 1 } },
        },
      ],
    });
    const next = buildDataPreviewFingerprint({
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: { a: 2 } },
        },
        {
          id: "src-b",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: { a: 1 } },
        },
      ],
    });
    expect(
      resolvePreviewRefreshSourceIds({
        previousFingerprint: prev,
        nextFingerprint: next,
        allFetchableIds: all,
        inputAffectedSourceIds: ["src-a"],
      }),
    ).toEqual(["src-a"]);
  });

  it("só viewLinks mudou → nenhum refetch", () => {
    const base: ComunicadoConfig = {
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: {} },
        },
        {
          id: "src-b",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: {} },
        },
        {
          id: "chart-1",
          type: "chart_view",
          chartType: "line",
          dataSourceId: "src-a",
          frame: { x: 0, y: 0, w: 20, h: 20 },
        },
      ],
    };
    const prev = buildDataPreviewFingerprint(base);
    const next = buildDataPreviewFingerprint({
      ...base,
      blocks: [
        base.blocks![0],
        base.blocks![1],
        {
          ...base.blocks![2],
          type: "chart_view",
          chartType: "line",
          dataSourceId: "src-b",
          frame: { x: 0, y: 0, w: 20, h: 20 },
        },
      ],
    });
    expect(prev).not.toBe(next);
    expect(
      resolvePreviewRefreshSourceIds({
        previousFingerprint: prev,
        nextFingerprint: next,
        allFetchableIds: ["src-a", "src-b"],
        inputAffectedSourceIds: ["src-a"],
      }),
    ).toEqual([]);
  });

  it("valor do input mudou → fontes afetadas", () => {
    const mk = (value: string): ComunicadoConfig => ({
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: {} },
        },
        {
          id: "input-1",
          type: "input",
          frame: { x: 0, y: 0, w: 20, h: 10 },
          input: { paramKey: "branch", defaultValue: value, targetScope: "slide" },
        },
      ],
    });
    const prev = buildDataPreviewFingerprint(mk("01"));
    const next = buildDataPreviewFingerprint(mk("02"));
    expect(
      resolvePreviewRefreshSourceIds({
        previousFingerprint: prev,
        nextFingerprint: next,
        allFetchableIds: all,
        inputAffectedSourceIds: ["src-a"],
      }),
    ).toEqual(["src-a"]);
  });

  it("dataFilters (ribbon) mudou → fontes afetadas pelo input", () => {
    const base: ComunicadoConfig = {
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: {} },
        },
      ],
    };
    const prev = buildDataPreviewFingerprint(base);
    const next = buildDataPreviewFingerprint({
      ...base,
      dataFilters: { branch: "02" },
    });
    expect(
      resolvePreviewRefreshSourceIds({
        previousFingerprint: prev,
        nextFingerprint: next,
        allFetchableIds: all,
        inputAffectedSourceIds: ["src-a"],
      }),
    ).toEqual(["src-a"]);
  });

  it("dataTransform da fonte entra no fingerprint", () => {
    const base: ComunicadoConfig = {
      blocks: [
        {
          id: "src-a",
          type: "data_source",
          frame: { x: 0, y: 0, w: 10, h: 10 },
          dataBinding: { operationId: "op", params: {} },
        },
      ],
    };
    const before = buildDataPreviewFingerprint(base);
    const after = buildDataPreviewFingerprint({
      ...base,
      blocks: [
        {
          ...base.blocks![0],
          type: "data_source",
          dataTransform: { steps: [{ op: "select", columns: ["a"] }] },
        },
      ],
    });
    expect(before).not.toBe(after);
  });
});
