import { describe, expect, it } from "vitest";

import { createChartViewBlock, createKpiViewBlock, createTableViewBlock } from "./comunicadoHelpers";
import type {
  ComunicadoChartViewBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "./comunicadoTypes";
import {
  scaleChartPartTypographyOnResize,
  scaleComplexBlockOnResize,
  scaleFontPx,
  scaleKpiPartTypographyOnResize,
  scaleTableOptionsFontSize,
  TABLE_VIEW_DEFAULT_FONT_SIZE_PX,
  uniformFrameScale,
} from "./scaleComplexBlockTypography";
import { upsertChartPartState } from "./comunicadoChartParts";
import { upsertKpiPartState } from "./comunicadoKpiParts";

describe("uniformFrameScale", () => {
  it("usa o menor eixo (evita tipografia esticada)", () => {
    expect(uniformFrameScale({ w: 10, h: 10 }, { w: 20, h: 40 })).toBe(2);
    expect(uniformFrameScale({ w: 10, h: 10 }, { w: 40, h: 20 })).toBe(2);
  });

  it("retorna 1 em no-op ou frames inválidos", () => {
    expect(uniformFrameScale({ w: 10, h: 10 }, { w: 10, h: 10 })).toBe(1);
    expect(uniformFrameScale({ w: 0, h: 10 }, { w: 20, h: 20 })).toBe(1);
  });
});

describe("scaleFontPx", () => {
  it("aplica fator e clamp", () => {
    expect(scaleFontPx(32, 2)).toBe(64);
    expect(scaleFontPx(10, 0.5)).toBe(6); // min 6
    expect(scaleFontPx(180, 2)).toBe(200); // max 200
  });
});

describe("scaleComplexBlockOnResize", () => {
  it("escala tipografia do KPI (value default 32)", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const next = scaleComplexBlockOnResize(block, { w: 20, h: 20 }, { w: 40, h: 40 }) as ComunicadoKpiViewBlock;
    expect(next.kpiParts?.value?.style?.fontSize).toBe(64);
    expect(next.kpiParts?.title?.style?.fontSize).toBe(28);
  });

  it("escala tipografia do gráfico", () => {
    const block = createChartViewBlock("line") as ComunicadoChartViewBlock;
    const next = scaleComplexBlockOnResize(block, { w: 30, h: 30 }, { w: 60, h: 60 }) as ComunicadoChartViewBlock;
    expect(next.chartParts?.title?.style?.fontSize).toBe(28);
    expect(next.chartParts?.legend?.style?.fontSize).toBe(20);
  });

  it("escala fontSize da tabela (default quando ausente)", () => {
    const block = createTableViewBlock(3, 3) as ComunicadoTableViewBlock;
    expect(block.tableOptions?.fontSize).toBeUndefined();
    const next = scaleComplexBlockOnResize(block, { w: 20, h: 20 }, { w: 40, h: 40 }) as ComunicadoTableViewBlock;
    expect(next.tableOptions?.fontSize).toBe(TABLE_VIEW_DEFAULT_FONT_SIZE_PX * 2);
  });

  it("no-op quando fator ≈ 1", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const next = scaleComplexBlockOnResize(block, { w: 20, h: 20 }, { w: 20.01, h: 20 });
    expect(next).toBe(block);
  });

  it("não altera bloco simples", () => {
    const block = {
      id: "t1",
      type: "text" as const,
      frame: { x: 0, y: 0, w: 20, h: 10 },
      content: "oi",
    };
    expect(scaleComplexBlockOnResize(block, { w: 20, h: 10 }, { w: 40, h: 20 })).toBe(block);
  });
});

describe("scalePartTypographyOnResize", () => {
  it("escala só a parte chart alvo", () => {
    let parts = upsertChartPartState({}, { kind: "title" }, { style: { fontSize: 14 } });
    parts = upsertChartPartState(parts, { kind: "legend" }, { style: { fontSize: 10 } });
    const next = scaleChartPartTypographyOnResize(
      parts,
      { kind: "title" },
      { w: 40, h: 10 },
      { w: 80, h: 20 },
    );
    expect(next.title?.style?.fontSize).toBe(28);
    expect(next.legend?.style?.fontSize).toBe(10);
  });

  it("escala tipografia da parte KPI", () => {
    const parts = upsertKpiPartState({}, { kind: "value" }, { style: { fontSize: 32 } });
    const next = scaleKpiPartTypographyOnResize(
      parts,
      { kind: "value" },
      { w: 50, h: 40 },
      { w: 25, h: 20 },
    );
    expect(next.value?.style?.fontSize).toBe(16);
  });
});

describe("scaleTableOptionsFontSize", () => {
  it("usa default quando ausente", () => {
    expect(scaleTableOptionsFontSize(undefined, 2)).toBe(24);
  });
});
