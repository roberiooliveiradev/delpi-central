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
  it("texto e título: visualBox (tipografia→forma) → exibição → organizar", () => {
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
      expect.arrayContaining(["visualBox", "display", "organize", "actions"]),
    );
    expect(text.indexOf("visualBox")).toBeLessThan(text.indexOf("display"));
    expect(text.indexOf("display")).toBeLessThan(text.indexOf("organize"));
    expect(text.indexOf("organize")).toBeLessThan(text.indexOf("actions"));
    expect(text).not.toContain("frame");
    expect(text).not.toContain("textBox");
    expect(text).not.toContain("shapeGallery");
  });

  it("ícone e imagem incluem display + organize + actions (não empty)", () => {
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
    ).toEqual(expect.arrayContaining(["shapeChrome", "display", "organize", "actions"]));

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
    ).toEqual(expect.arrayContaining(["media", "imageCrop", "display", "organize", "actions"]));
  });

  it("fonte de dados aponta para hint + display", () => {
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
    ).toEqual(expect.arrayContaining(["dataSourceHint", "display", "organize", "actions"]));
  });

  it("multi-seleção: alinhar + organize + actions", () => {
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
    ).toEqual(["alignMulti", "organize", "actions"]);
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
        "display",
        "organize",
        "actions",
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
    ).toEqual(expect.arrayContaining(["shapeChrome", "typography", "display", "organize", "actions"]));
  });

  it("forma tipada: mesma ordem visualBox (tipografia→forma) + display", () => {
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
      "visualBox",
      "display",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("tabela tipada: design + layout + display", () => {
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
      "tableLayoutData",
      "tableLayoutDisplay",
      "tableLayoutAlign",
      "display",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("host cobre tipografia, visualBox, tabela, chart, kpi, media, partFormat e input", () => {
    for (const id of [
      "typography",
      "textBox",
      "visualBox",
      "display",
      "shapeGallery",
      "shapeChrome",
      "tableStyleOptions",
      "tableStyles",
      "tableBorders",
      "tableLayoutData",
      "tableLayoutDisplay",
      "tableLayoutAlign",
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
