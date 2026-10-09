import { describe, expect, it } from "vitest";

import {
  DEFAULT_TICKET_LIST_FILTERS,
  parseTicketListFilters,
} from "./ticketView";
import {
  cellTextForColumn,
  defaultTicketListColumnPreferences,
  TICKET_LIST_COLUMN_CATALOG,
  formatTicketSortLevels,
  parseTicketSortLevels,
  resolveVisibleColumns,
  ticketListFiltersFromFilterGroup,
  ticketListViewModelFromFilters,
} from "./ticketListViewModel";
import type { TicketSummary } from "../api/helpdeskApi";

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

describe("parseTicketSortLevels / formatTicketSortLevels", () => {
  it("aceita até três níveis e ignora campo inválido", () => {
    expect(parseTicketSortLevels("updated_at:desc,title:asc,status:asc")).toEqual([
      { field: "updated_at", direction: "desc" },
      { field: "title", direction: "asc" },
      { field: "status", direction: "asc" },
    ]);
    expect(parseTicketSortLevels("updated_at:desc,entity:asc,title:asc")).toEqual([
      { field: "updated_at", direction: "desc" },
      { field: "title", direction: "asc" },
    ]);
  });

  it("serializa multi-sort para a URL", () => {
    expect(
      formatTicketSortLevels([
        { field: "updated_at", direction: "desc" },
        { field: "title", direction: "asc" },
      ]),
    ).toBe("updated_at:desc,title:asc");
  });
});

describe("ticketListFiltersFromFilterGroup", () => {
  it("achata regras AND no recorte plano", () => {
    const next = ticketListFiltersFromFilterGroup(
      {
        id: "root",
        combinator: "and",
        rules: [
          { id: "1", field: "q", operator: "contains", value: "rede" },
          { id: "2", field: "status", operator: "eq", value: "open" },
          { id: "3", field: "created_from", operator: "gte", value: "2026-01-01" },
        ],
        groups: [],
      },
      DEFAULT_TICKET_LIST_FILTERS,
    );
    expect(next.q).toBe("rede");
    expect(next.status).toBe("open");
    expect(next.created_from).toBe("2026-01-01");
    expect(next.page).toBe(1);
  });

  it("não serializa grupo OR aninhado", () => {
    const next = ticketListFiltersFromFilterGroup(
      {
        id: "root",
        combinator: "and",
        rules: [{ id: "1", field: "status", operator: "eq", value: "open" }],
        groups: [
          {
            id: "or-1",
            combinator: "or",
            rules: [{ id: "2", field: "q", operator: "contains", value: "ignorar" }],
            groups: [],
          },
        ],
      },
      DEFAULT_TICKET_LIST_FILTERS,
    );
    expect(next.status).toBe("open");
    expect(next.q).toBe("");
  });
});

describe("cellTextForColumn", () => {
  const row: TicketSummary = {
    id: 1120,
    title: "Monitor",
    status: "Novo",
    category: "Hardware",
    urgency: "Média",
    updated_at: "2026-09-21T12:00:00Z",
    created_at: "2026-09-21T10:00:00Z",
    assigned_display_name: "Ana Silva",
    requester_display_name: "Robério Teixeira",
  };

  it("publica o requerente da lista (G-05)", () => {
    expect(cellTextForColumn(row, "requester")).toBe("Robério Teixeira");
    expect(cellTextForColumn(row, "assigned")).toBe("Ana Silva");
  });

  it("não inventa nome quando o BFF omite o campo", () => {
    const withoutRequester = { ...row, requester_display_name: undefined };
    expect(cellTextForColumn(withoutRequester, "requester")).toBe("");
  });

  it("publica código GLPI do requerente quando o BFF entrega o id", () => {
    const withId = { ...row, requester_id: 11 };
    expect(cellTextForColumn(withId, "requester")).toBe("Robério Teixeira (#11)");
  });

  it("publica entidade e última edição vindas do GLPI", () => {
    const full = { ...row, entity: "Entidade raiz", last_editor: "Ana Silva" };
    expect(cellTextForColumn(full, "entity")).toBe("Entidade raiz");
    expect(cellTextForColumn(full, "last_editor")).toBe("Ana Silva");
    const without = { ...row };
    expect(cellTextForColumn(without, "entity")).toBe("");
    expect(cellTextForColumn(without, "last_editor")).toBe("");
  });
});

describe("TICKET_LIST_COLUMN_CATALOG", () => {
  it("requerente visível por padrão para qualquer solicitante", () => {
    const requester = TICKET_LIST_COLUMN_CATALOG.find((column) => column.key === "requester");
    expect(requester?.solicitante).toBe(true);
    expect(requester?.defaultVisible).toBe(true);
  });

  it("entidade e última edição entram no seletor do solicitante", () => {
    const entity = TICKET_LIST_COLUMN_CATALOG.find((column) => column.key === "entity");
    const editor = TICKET_LIST_COLUMN_CATALOG.find((column) => column.key === "last_editor");
    expect(entity?.solicitante).toBe(true);
    expect(editor?.solicitante).toBe(true);
    expect(entity?.defaultVisible).toBe(false);
    expect(editor?.defaultVisible).toBe(false);
  });

  it("resolveVisibleColumns inclui requerente por padrão", () => {
    const keys = resolveVisibleColumns().map((column) => column.key);
    expect(keys).toContain("requester");
  });
});
