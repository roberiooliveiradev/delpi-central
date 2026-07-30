import { describe, expect, it } from "vitest";
import {
  DEFAULT_COMUNICADO_TABLE_OPTIONS,
  isTableElementEnabled,
  mergeComunicadoTableOptions,
} from "@delpi/tv-dashboard-presentation";

import {
  applyTableAddElementChoice,
  isTableAddElementChoiceActive,
  resolveTableAddElementMenuRoots,
} from "./tableAddElementMenuCatalog";

describe("tableAddElementMenuCatalog", () => {
  it("expõe as 8 opções de estilo com Mostrar/Ocultar", () => {
    const roots = resolveTableAddElementMenuRoots();
    expect(roots.map((root) => root.elementId)).toEqual([
      "tableTitle",
      "header",
      "totalRow",
      "firstColumn",
      "lastColumn",
      "zebraStripe",
      "bandedColumns",
      "borders",
    ]);
    for (const root of roots) {
      expect(root.choices.map((choice) => choice.label)).toEqual(["Mostrar", "Ocultar"]);
      expect(root.icon).toBeTruthy();
      expect(root.moreOptionsLabel).toMatch(/Mais opções/);
    }
  });

  it("aplica choice e marca ativo o estado correspondente", () => {
    const off = mergeComunicadoTableOptions(
      applyTableAddElementChoice("header:off", DEFAULT_COMUNICADO_TABLE_OPTIONS),
    );
    expect(isTableElementEnabled("header", off)).toBe(false);
    expect(isTableAddElementChoiceActive("header:off", off)).toBe(true);
    expect(isTableAddElementChoiceActive("header:on", off)).toBe(false);

    const on = mergeComunicadoTableOptions(applyTableAddElementChoice("zebraStripe:on", off));
    expect(isTableElementEnabled("zebraStripe", on)).toBe(true);
    expect(isTableAddElementChoiceActive("zebraStripe:on", on)).toBe(true);
  });
});
