import { describe, expect, it } from "vitest";

import { DEFAULT_CONFIGURABLE_TABLE_OPTIONS, mergeConfigurableTableOptions } from "./configurableTableOptions";
import {
  CONFIGURABLE_TABLE_ELEMENT_CATALOG,
  isConfigurableTableElementEnabled,
  setConfigurableTableElementEnabled,
} from "./configurableTableElementCatalog";

describe("configurableTableElementCatalog", () => {
  it("lista elementos configuráveis da tabela", () => {
    const labels = CONFIGURABLE_TABLE_ELEMENT_CATALOG.map((entry) => entry.label);
    expect(labels).toContain("Título da tabela");
    expect(labels).toContain("Cabeçalho");
    expect(labels).toContain("Listras alternadas");
  });

  it("ativa e desativa cabeçalho", () => {
    const enabled = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("header", true));
    expect(isConfigurableTableElementEnabled("header", enabled)).toBe(true);
    const disabled = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("header", false));
    expect(isConfigurableTableElementEnabled("header", disabled)).toBe(false);
  });

  it("listras alternadas desligadas por padrão no preset grid", () => {
    expect(isConfigurableTableElementEnabled("zebraStripe", DEFAULT_CONFIGURABLE_TABLE_OPTIONS)).toBe(false);
    const on = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("zebraStripe", true));
    expect(isConfigurableTableElementEnabled("zebraStripe", on)).toBe(true);
  });
});
