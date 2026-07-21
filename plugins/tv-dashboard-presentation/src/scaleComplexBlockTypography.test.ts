import { describe, expect, it } from "vitest";

import { createChartViewBlock, createKpiViewBlock, createTableViewBlock } from "./comunicadoHelpers";
import type {
  ComunicadoChartViewBlock,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "./comunicadoTypes";
import {
  applyComplexBlockFrameWithTypography,
  contentFillFrameScale,
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

describe("contentFillFrameScale", () => {
  it("cresce ao alongar só a altura (média geométrica)", () => {
    expect(contentFillFrameScale({ w: 10, h: 10 }, { w: 10, h: 40 })).toBe(2);
    expect(contentFillFrameScale({ w: 12, h: 7 }, { w: 12, h: 28 })).toBe(2);
  });

  it("uniform e fill coincidem em escala isótropa", () => {
    expect(contentFillFrameScale({ w: 10, h: 10 }, { w: 20, h: 20 })).toBe(2);
    expect(uniformFrameScale({ w: 10, h: 10 }, { w: 20, h: 20 })).toBe(2);
  });
});

describe("scaleFontPx", () => {
  it("aplica fator e só piso mínimo", () => {
    expect(scaleFontPx(32, 2)).toBe(64);
    expect(scaleFontPx(10, 0.5)).toBe(12); // min alinhado a COMUNICADO_FONT_SIZE_MIN
    expect(scaleFontPx(180, 2)).toBe(360); // sem teto
  });
});

describe("scaleComplexBlockOnResize", () => {
  it("escala tipografia do KPI (título/ícone; valor fica auto-fit)", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const next = scaleComplexBlockOnResize(block, { w: 20, h: 20 }, { w: 40, h: 40 }) as ComunicadoKpiViewBlock;
    expect(next.kpiParts?.value?.style?.fontSize).toBeUndefined();
    expect(next.kpiParts?.title?.style?.fontSize).toBe(36);
    expect(next.kpiParts?.icon?.style?.iconSize).toBe(72);
  });

  it("KPI alongado só na altura ainda escala título/ícone", () => {
    const block = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const next = scaleComplexBlockOnResize(
      block,
      { w: 12, h: 7 },
      { w: 12, h: 28 },
    ) as ComunicadoKpiViewBlock;
    expect(next.kpiParts?.title?.style?.fontSize).toBe(36);
    expect(next.kpiParts?.icon?.style?.iconSize).toBe(72);
    expect(next.kpiParts?.value?.style?.fontSize).toBeUndefined();
  });

  it("escala tipografia do gráfico", () => {
    const block = createChartViewBlock("line") as ComunicadoChartViewBlock;
    const next = scaleComplexBlockOnResize(block, { w: 30, h: 30 }, { w: 60, h: 60 }) as ComunicadoChartViewBlock;
    expect(next.chartParts?.title?.style?.fontSize).toBe(44);
    expect(next.chartParts?.legend?.style?.fontSize).toBe(32);
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

  it("escala tipografia da parte KPI (valor limpa fontSize para auto-fit)", () => {
    const parts = upsertKpiPartState({}, { kind: "value" }, { style: { fontSize: 32 } });
    const next = scaleKpiPartTypographyOnResize(
      parts,
      { kind: "value" },
      { w: 50, h: 40 },
      { w: 25, h: 20 },
    );
    expect(next.value?.style?.fontSize).toBeUndefined();
  });
});

describe("scaleTableOptionsFontSize", () => {
  it("usa default quando ausente", () => {
    expect(scaleTableOptionsFontSize(undefined, 2)).toBe(TABLE_VIEW_DEFAULT_FONT_SIZE_PX * 2);
  });
});

describe("applyComplexBlockFrameWithTypography (live a partir do baseline)", () => {
  it("reescala KPI/chart/table do baseline; não dobrar fator no finalize", () => {
    const kpi = createKpiViewBlock() as ComunicadoKpiViewBlock;
    const mid = applyComplexBlockFrameWithTypography(kpi, {
      ...kpi.frame,
      w: kpi.frame.w * 1.5,
      h: kpi.frame.h * 1.5,
    }) as ComunicadoKpiViewBlock;
    const endFrame = { ...kpi.frame, w: kpi.frame.w * 2, h: kpi.frame.h * 2 };
    const end = applyComplexBlockFrameWithTypography(kpi, endFrame) as ComunicadoKpiViewBlock;
    expect(mid.kpiParts?.value?.style?.fontSize).toBeUndefined();
    expect(mid.kpiParts?.title?.style?.fontSize).toBe(27);
    expect(end.kpiParts?.value?.style?.fontSize).toBeUndefined();
    expect(end.kpiParts?.title?.style?.fontSize).toBe(36);
    /* Bug antigo: tipografia já escalada + fator origin→final → dobra de novo. */
    const doubled = scaleComplexBlockOnResize(end, kpi.frame, endFrame) as ComunicadoKpiViewBlock;
    expect(doubled.kpiParts?.title?.style?.fontSize).toBe(72);
    const finalizeOk = applyComplexBlockFrameWithTypography(kpi, endFrame) as ComunicadoKpiViewBlock;
    expect(finalizeOk.kpiParts?.title?.style?.fontSize).toBe(36);
    expect(finalizeOk.kpiParts?.value?.style?.fontSize).toBeUndefined();

    const chart = createChartViewBlock("bar") as ComunicadoChartViewBlock;
    const chartEnd = applyComplexBlockFrameWithTypography(chart, {
      ...chart.frame,
      w: chart.frame.w * 2,
      h: chart.frame.h * 2,
    }) as ComunicadoChartViewBlock;
    expect(chartEnd.chartParts?.title?.style?.fontSize).toBe(44);

    const table = createTableViewBlock(2, 2) as ComunicadoTableViewBlock;
    const tableEnd = applyComplexBlockFrameWithTypography(table, {
      ...table.frame,
      w: table.frame.w * 2,
      h: table.frame.h * 2,
    }) as ComunicadoTableViewBlock;
    expect(tableEnd.tableOptions?.fontSize).toBe(TABLE_VIEW_DEFAULT_FONT_SIZE_PX * 2);
  });
});
