import { beforeEach, describe, expect, it } from "vitest";

import {
  filterRecentsByCaps,
  pushRecentView,
  readRecentViews,
} from "./homeRecentViews";

const STORAGE_KEY = "controllership-finance.home.recentViews.v1";

beforeEach(() => {
  window.localStorage.clear();
});

describe("homeRecentViews", () => {
  it("push adiciona e lê de volta", () => {
    pushRecentView({ viewId: "entry_audit", label: "Auditoria de Entradas" });
    const items = readRecentViews();
    expect(items.length).toBe(1);
    expect(items[0].viewId).toBe("entry_audit");
  });

  it("deduplica pela chave viewId+search", () => {
    pushRecentView({ viewId: "monthly_closing", label: "Fechamento mensal" });
    pushRecentView({ viewId: "monthly_closing", label: "Fechamento mensal" });
    pushRecentView({
      viewId: "monthly_closing",
      search: "tab=documents",
      label: "Documentos",
    });
    const items = readRecentViews();
    expect(items.length).toBe(2);
  });

  it("respeita o limite de 5 entradas", () => {
    const views = [
      "entry_audit",
      "checklist_admin",
      "documents_admin",
      "catalogs_admin",
      "received_documents",
    ] as const;
    for (let i = 0; i < 8; i++) {
      pushRecentView({
        viewId: views[i % views.length],
        search: i >= views.length ? `?x=${i}` : undefined,
        label: `R${i}`,
      });
    }
    const items = readRecentViews();
    expect(items.length).toBe(5);
  });

  it("tolera storage corrompido retornando lista vazia", () => {
    window.localStorage.setItem(STORAGE_KEY, "not-json{{{");
    expect(readRecentViews()).toEqual([]);

    window.localStorage.setItem(STORAGE_KEY, JSON.stringify({ a: 1 }));
    expect(readRecentViews()).toEqual([]);
  });

  it("descarta Início e views fora do catálogo (D7)", () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([
        { viewId: "overview", label: "X", at: 1 },
        { viewId: "home", label: "Início", at: 2 },
        { viewId: "entry_audit", label: "Auditoria", at: 3 },
      ]),
    );
    const items = readRecentViews();
    expect(items.length).toBe(1);
    expect(items[0].viewId).toBe("entry_audit");
  });

  it("não armazena tokens nem payloads — só viewId/search/label/at", () => {
    pushRecentView({
      viewId: "entry_audit",
      label: "Auditoria",
    } as never);
    const raw = window.localStorage.getItem(STORAGE_KEY) ?? "";
    expect(raw).not.toContain("token");
    expect(raw).not.toContain("Bearer");
    expect(raw).not.toContain("authorization");
  });

  it("filterRecentsByCaps filtra por capacidade do catálogo", () => {
    const items = pushRecentView({
      viewId: "entry_audit",
      label: "Auditoria",
    });
    expect(
      filterRecentsByCaps(items, {
        access: true,
        manage: false,
        accessDre: false,
        lnfAccess: false,
      }).length,
    ).toBe(1);
    expect(
      filterRecentsByCaps(items, {
        access: false,
        manage: false,
        accessDre: true,
        lnfAccess: false,
      }).length,
    ).toBe(0);
  });
});
