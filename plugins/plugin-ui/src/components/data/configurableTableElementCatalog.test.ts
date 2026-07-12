import { describe, expect, it } from "vitest";

import { DEFAULT_CONFIGURABLE_TABLE_OPTIONS, mergeConfigurableTableOptions } from "./configurableTableOptions";
import {
  CONFIGURABLE_TABLE_ELEMENT_CATALOG,
  isConfigurableTableElementEnabled,
  setConfigurableTableElementEnabled,
} from "./configurableTableElementCatalog";

describe("configurableTableElementCatalog", () => {
  it("lista opções de estilo alinhadas ao Excel Table Design", () => {
    const ids = CONFIGURABLE_TABLE_ELEMENT_CATALOG.map((entry) => entry.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "tableTitle",
        "header",
        "totalRow",
        "zebraStripe",
        "firstColumn",
        "lastColumn",
        "bandedColumns",
        "borders",
      ]),
    );
  });

  it("ativa e desativa cabeçalho", () => {
    const enabled = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("header", true));
    expect(isConfigurableTableElementEnabled("header", enabled)).toBe(true);
    const disabled = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("header", false));
    expect(isConfigurableTableElementEnabled("header", disabled)).toBe(false);
  });

  it("listras nas linhas desligadas por padrão no preset grid", () => {
    expect(isConfigurableTableElementEnabled("zebraStripe", DEFAULT_CONFIGURABLE_TABLE_OPTIONS)).toBe(false);
    const on = mergeConfigurableTableOptions(setConfigurableTableElementEnabled("zebraStripe", true));
    expect(isConfigurableTableElementEnabled("zebraStripe", on)).toBe(true);
  });

  it("liga total, primeira/última coluna e listras de coluna", () => {
    const patched = mergeConfigurableTableOptions({
      ...setConfigurableTableElementEnabled("totalRow", true),
      ...setConfigurableTableElementEnabled("firstColumn", true),
      ...setConfigurableTableElementEnabled("lastColumn", true),
      ...setConfigurableTableElementEnabled("bandedColumns", true),
    });
    expect(isConfigurableTableElementEnabled("totalRow", patched)).toBe(true);
    expect(isConfigurableTableElementEnabled("firstColumn", patched)).toBe(true);
    expect(isConfigurableTableElementEnabled("lastColumn", patched)).toBe(true);
    expect(isConfigurableTableElementEnabled("bandedColumns", patched)).toBe(true);
  });
});
