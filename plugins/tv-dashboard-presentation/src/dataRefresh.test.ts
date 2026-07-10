import { describe, expect, it } from "vitest";

import { buildDataPreviewFingerprint, resolveDataBlockRefreshSec } from "./dataRefresh";
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
});
