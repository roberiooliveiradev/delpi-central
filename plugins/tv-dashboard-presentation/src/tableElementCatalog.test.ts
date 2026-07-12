import { describe, expect, it } from "vitest";

import { DEFAULT_COMUNICADO_TABLE_OPTIONS, mergeComunicadoTableOptions } from "./comunicadoTableOptions";
import {
  TABLE_ELEMENT_CATALOG,
  isTableElementEnabled,
  setTableElementEnabled,
} from "./tableElementCatalog";

describe("tableElementCatalog", () => {
  it("lista elementos configuráveis da tabela", () => {
    const labels = TABLE_ELEMENT_CATALOG.map((entry) => entry.label);
    expect(labels).toContain("Título da tabela");
    expect(labels).toContain("Linha de cabeçalho");
    expect(labels).toContain("Listras nas linhas");
    expect(labels).toContain("Linha de totais");
  });

  it("ativa e desativa cabeçalho", () => {
    const enabled = mergeComunicadoTableOptions(setTableElementEnabled("header", true));
    expect(isTableElementEnabled("header", enabled)).toBe(true);
    const disabled = mergeComunicadoTableOptions(setTableElementEnabled("header", false));
    expect(isTableElementEnabled("header", disabled)).toBe(false);
  });

  it("listras nas linhas desligadas por padrão no preset grid", () => {
    expect(isTableElementEnabled("zebraStripe", DEFAULT_COMUNICADO_TABLE_OPTIONS)).toBe(false);
    const on = mergeComunicadoTableOptions(setTableElementEnabled("zebraStripe", true));
    expect(isTableElementEnabled("zebraStripe", on)).toBe(true);
  });
});
