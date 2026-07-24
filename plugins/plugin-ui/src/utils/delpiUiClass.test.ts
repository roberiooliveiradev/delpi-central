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

describe("ensureDelpiUiClass", () => {
  it("injeta canônico quando o MFE passa só o prefixo", async () => {
    const { ensureDelpiUiClass } = await import("./delpiUiClass");
    expect(ensureDelpiUiClass("ef-export-actions", "delpi-ui-export-actions")).toBe(
      "ef-export-actions delpi-ui-export-actions",
    );
    expect(ensureDelpiUiClass("delpi-ui-export-actions", "delpi-ui-export-actions")).toBe(
      "delpi-ui-export-actions",
    );
    expect(ensureDelpiUiClass(undefined, "delpi-ui-export-actions")).toBe(
      "delpi-ui-export-actions",
    );
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

describe("resolveDataTableColumnClassName", () => {
  it("espelha {prefix}-table__col--* para delpi-ui-table__col--*", async () => {
    const { resolveDataTableColumnClassName } = await import("./delpiUiClass");
    expect(resolveDataTableColumnClassName("pa-table__col--numeric")).toBe(
      "pa-table__col--numeric delpi-ui-table__col--numeric",
    );
    expect(resolveDataTableColumnClassName("pa-table__col--wide")).toBe(
      "pa-table__col--wide delpi-ui-table__col--wide",
    );
    expect(resolveDataTableColumnClassName("ds-table__col--wrap")).toBe(
      "ds-table__col--wrap delpi-ui-table__col--wrap",
    );
    expect(
      resolveDataTableColumnClassName("pa-table__col--numeric delpi-ui-table__col--numeric"),
    ).toBe("pa-table__col--numeric delpi-ui-table__col--numeric");
    expect(resolveDataTableColumnClassName(undefined)).toBeUndefined();
    expect(resolveDataTableColumnClassName("ds-table__actions-col")).toBe(
      "ds-table__actions-col delpi-ui-table__actions-col",
    );
    expect(resolveDataTableColumnClassName("ds-table__actions-col--wide")).toBe(
      "ds-table__actions-col--wide delpi-ui-table__actions-col--wide",
    );
  });
});

describe("ghostBtnBemClasses", () => {
  it("emite dual-class e modificadores", async () => {
    const { ghostBtnBemClasses, ghostBtnWithModifiers } = await import("./ghostBtnBem");
    expect(ghostBtnBemClasses("pac")).toBe("pac-ghost-btn delpi-ui-ghost-btn");
    expect(ghostBtnWithModifiers("pac", "icon", "danger")).toContain("delpi-ui-ghost-btn--icon");
    expect(ghostBtnWithModifiers("pac", "icon", "danger")).toContain("pac-ghost-btn--danger");
  });
});

describe("kits DataTable/Pagination — classes delpi-ui", () => {
  it("Pagination expõe controles em linha via delpi-ui-pagination*", () => {
    const { pagination, tablePageSize } = paginationBemClasses("dc");
    expect(pagination.root).toContain("delpi-ui-pagination");
    expect(pagination.controls).toContain("delpi-ui-pagination__controls");
    expect(pagination.action).toContain("delpi-ui-pagination__action");
    expect(pagination.actionHelp).toContain("delpi-ui-pagination__action-help");
    expect(pagination.infoHelp).toContain("delpi-ui-pagination__help");
    expect(pagination.jumpHelp).toContain("delpi-ui-pagination__jump-help");
    expect(pagination.ghostBtn).toContain("delpi-ui-ghost-btn");
    expect(tablePageSize.root).toContain("delpi-ui-table-page-size");
    expect(tablePageSize.help).toContain("delpi-ui-table-page-size__help");
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
    expect(table.sortableTable).toContain("delpi-ui-table--sortable");
    expect(table.compactTable).toContain("delpi-ui-table--compact");
    expect(table.colNumeric).toContain("delpi-ui-table__col--numeric");
    expect(table.colWide).toContain("delpi-ui-table__col--wide");
    expect(table.colActions).toContain("delpi-ui-table__actions-col");
    expect(table.actions).toContain("delpi-ui-table__actions");
    expect(table.sub).toContain("delpi-ui-table__sub");
    expect(table.rowEditing).toContain("delpi-ui-table__row--editing");
  });
});
