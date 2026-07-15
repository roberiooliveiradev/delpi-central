import { describe, expect, it } from "vitest";

import { dataTableBemClasses } from "../components/data/DataTable";
import { dataTableSectionBemClasses } from "../components/data/DataTableSection";
import { paginationBemClasses } from "../components/data/Pagination";
import { delpiUiClass } from "./delpiUiClass";

describe("delpiUiClass", () => {
  it("junta BEM do plugin com classe estável canônica", () => {
    expect(delpiUiClass("dc-pagination", "delpi-ui-pagination")).toBe(
      "dc-pagination delpi-ui-pagination",
    );
  });

  it("não duplica quando prefixo e canônico são iguais", () => {
    expect(delpiUiClass("delpi-ui-select", "delpi-ui-select")).toBe("delpi-ui-select");
  });
});

describe("withBemModifier", () => {
  it("aplica modificador em cada token BEM", async () => {
    const { withBemModifier } = await import("./delpiUiClass");
    expect(withBemModifier("dp-kpi-badge delpi-ui-kpi-badge", "scope")).toBe(
      "dp-kpi-badge dp-kpi-badge--scope delpi-ui-kpi-badge delpi-ui-kpi-badge--scope",
    );
  });
});

describe("kits DataTable/Pagination — classes delpi-ui", () => {
  it("Pagination expõe controles em linha via delpi-ui-pagination*", () => {
    const { pagination, tablePageSize } = paginationBemClasses("dc");
    expect(pagination.root).toContain("delpi-ui-pagination");
    expect(pagination.controls).toContain("delpi-ui-pagination__controls");
    expect(pagination.ghostBtn).toContain("delpi-ui-ghost-btn");
    expect(tablePageSize.root).toContain("delpi-ui-table-page-size");
  });

  it("DataTableSection toolbar/search usam delpi-ui-*", () => {
    const section = dataTableSectionBemClasses("pa");
    expect(section.toolbar).toContain("delpi-ui-table-toolbar");
    expect(section.search).toContain("delpi-ui-table-search");
    expect(section.header).toContain("delpi-ui-table-section__header");
  });

  it("DataTable sort-button usa delpi-ui-table__sort-button", () => {
    const table = dataTableBemClasses("dp");
    expect(table.sortButton).toContain("delpi-ui-table__sort-button");
    expect(table.wrapSection).toContain("delpi-ui-table-wrap--section");
  });
});
