import { describe, expect, it } from "vitest";

import {
  DEFAULT_TICKET_LIST_FILTERS,
  parseTicketListFilters,
} from "./ticketView";
import {
  defaultTicketListColumnPreferences,
  resolveVisibleColumns,
  ticketListViewModelFromFilters,
} from "./ticketListViewModel";

describe("ticketListViewModelFromFilters", () => {
  it("monta regras a partir do recorte plano da URL", () => {
    const model = ticketListViewModelFromFilters(
      parseTicketListFilters("?status=open&q=rede&sort=created_at:asc"),
    );
    expect(model.filterRoot.combinator).toBe("and");
    expect(model.filterRoot.rules.map((rule) => rule.field)).toEqual(["q", "status"]);
    expect(model.sorts).toEqual([{ field: "created_at", direction: "asc" }]);
    expect(model.activeFilterLabels).toContain("Busca");
    expect(model.activeFilterLabels.some((label) => label.startsWith("Status:"))).toBe(true);
    expect(model.primarySortLabel).toContain("Aberto");
    expect(model.viewMode).toBe("table");
  });

  it("mantém o default de ordenação quando a URL não traz sort", () => {
    const model = ticketListViewModelFromFilters(DEFAULT_TICKET_LIST_FILTERS);
    expect(model.sorts[0]).toEqual({ field: "updated_at", direction: "desc" });
    expect(model.filterRoot.rules).toEqual([]);
  });
});

describe("resolveVisibleColumns", () => {
  it("sempre inclui colunas fixas do solicitante", () => {
    const prefs = defaultTicketListColumnPreferences().map((column) =>
      column.key === "title" ? { ...column, visible: false } : column,
    );
    const visible = resolveVisibleColumns(prefs).map((column) => column.key);
    expect(visible).toContain("id");
    expect(visible).toContain("title");
    expect(visible).not.toContain("entity");
    expect(visible).not.toContain("last_editor");
  });

  it("respeita preferência de ocultar coluna opcional", () => {
    const prefs = defaultTicketListColumnPreferences().map((column) =>
      column.key === "urgency" ? { ...column, visible: false } : column,
    );
    expect(resolveVisibleColumns(prefs).map((column) => column.key)).not.toContain("urgency");
  });
});
