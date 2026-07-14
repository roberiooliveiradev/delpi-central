import { describe, expect, it } from "vitest";

import {
  resolveSelectionSections,
  SHARED_HOST_SECTIONS,
} from "./resolveSelectionSections";
import type { SelectionSectionContext } from "./types";

function ctx(
  partial: Partial<SelectionSectionContext> & {
    selected: SelectionSectionContext["selected"];
  },
): SelectionSectionContext {
  return {
    selectedIds: partial.selected ? [partial.selected.id] : [],
    ...partial,
  };
}

describe("resolveSelectionSections", () => {
  it("texto e título compartilham tipografia + frame + organize", () => {
    const text = resolveSelectionSections(
      ctx({
        selected: {
          id: "t1",
          type: "text",
          content: "Olá",
          frame: { x: 0, y: 0, w: 20, h: 10 },
        } as SelectionSectionContext["selected"],
      }),
    );
    expect(text).toEqual(
      expect.arrayContaining(["typography", "textBox", "frame", "organize"]),
    );
  });

  it("ícone e imagem incluem frame + organize (não empty)", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "i1",
            type: "icon",
            iconName: "Package",
            frame: { x: 0, y: 0, w: 10, h: 10 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual(expect.arrayContaining(["shapeChrome", "frame", "organize"]));

    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "m1",
            type: "image",
            frame: { x: 0, y: 0, w: 20, h: 20 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual(expect.arrayContaining(["media", "imageCrop", "frame", "organize"]));
  });

  it("fonte de dados aponta para hint + frame", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "d1",
            type: "data_source",
            frame: { x: 0, y: 0, w: 20, h: 20 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual(expect.arrayContaining(["dataSourceHint", "frame", "organize"]));
  });

  it("multi-seleção: alinhar + organize", () => {
    expect(
      resolveSelectionSections({
        selected: {
          id: "a",
          type: "text",
          content: "A",
          frame: { x: 0, y: 0, w: 10, h: 10 },
        } as SelectionSectionContext["selected"],
        selectedIds: ["a", "b"],
      }),
    ).toEqual(["alignMulti", "organize"]);
  });

  it("parte de gráfico prioriza partFormat + tipografia", () => {
    const sections = resolveSelectionSections(
      ctx({
        selected: {
          id: "c1",
          type: "chart_view",
          frame: { x: 0, y: 0, w: 40, h: 30 },
        } as SelectionSectionContext["selected"],
        selectedChartPart: { kind: "title" },
      }),
    );
    expect(sections[0]).toBe("partFormat");
    expect(sections).toContain("typography");
    expect(sections).toContain("organize");
  });

  it("gráfico tipado inclui layout/estilos/tipo/rótulos/eixos/série", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "c2",
            type: "chart_view",
            frame: { x: 0, y: 0, w: 40, h: 30 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual(
      expect.arrayContaining([
        "typography",
        "chartLayout",
        "chartStyles",
        "chartType",
        "chartLabels",
        "chartAxes",
        "chartSeries",
        "frame",
        "organize",
      ]),
    );
  });

  it("parte de KPI inclui shapeChrome + tipografia", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "k1",
            type: "kpi_view",
            frame: { x: 0, y: 0, w: 20, h: 15 },
          } as SelectionSectionContext["selected"],
          selectedKpiPart: { kind: "title" },
        }),
      ),
    ).toEqual(expect.arrayContaining(["shapeChrome", "typography", "organize"]));
  });

  it("forma tipada: galeria + chrome + tipografia + frame", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "s1",
            type: "shape",
            shape: "rectangle",
            frame: { x: 0, y: 0, w: 20, h: 20 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual([
      "shapeGallery",
      "shapeChrome",
      "typography",
      "frame",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("tabela tipada: opções + estilos + bordas + frame", () => {
    expect(
      resolveSelectionSections(
        ctx({
          selected: {
            id: "tb1",
            type: "table_view",
            frame: { x: 0, y: 0, w: 40, h: 30 },
          } as SelectionSectionContext["selected"],
        }),
      ),
    ).toEqual([
      "tableStyleOptions",
      "tableStyles",
      "tableBorders",
      "frame",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("host cobre tipografia, tabela, chart, kpi, media, partFormat e input", () => {
    for (const id of [
      "typography",
      "textBox",
      "shapeGallery",
      "shapeChrome",
      "tableStyleOptions",
      "tableStyles",
      "tableBorders",
      "chartLayout",
      "chartStyles",
      "chartType",
      "chartLabels",
      "chartAxes",
      "chartSeries",
      "kpiAppearance",
      "media",
      "imageCrop",
      "canvasTable",
      "partFormat",
      "inputBinding",
      "animation",
      "actions",
    ] as const) {
      expect(SHARED_HOST_SECTIONS.has(id)).toBe(true);
    }
  });
});
