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
    pushRecentView({ viewId: "home", label: "Início" });
    const items = readRecentViews();
    expect(items.length).toBe(1);
    expect(items[0].viewId).toBe("home");
    expect(items[0].label).toBe("Início");
  });

  it("deduplica pela chave viewId+search", () => {
    pushRecentView({ viewId: "home", label: "Início" });
    pushRecentView({ viewId: "home", label: "Início" });
    pushRecentView({ viewId: "home", search: "?q=a", label: "Início" });
    const items = readRecentViews();
    expect(items.length).toBe(2);
  });

  it("respeita o limite de 5 entradas", () => {
    for (let i = 0; i < 8; i++) {
      pushRecentView({ viewId: "home", search: `?q=${i}`, label: `R${i}` });
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

  it("descarta itens de views que não existem no catálogo", () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify([
        { viewId: "overview", label: "X", at: 1 },
        { viewId: "home", label: "Início", at: 2 },
      ]),
    );
    const items = readRecentViews();
    expect(items.length).toBe(1);
    expect(items[0].viewId).toBe("home");
  });

  it("não armazena tokens nem payloads — só viewId/search/label/at", () => {
    pushRecentView({
      viewId: "home",
      label: "Início",
    } as never);
    const raw = window.localStorage.getItem(STORAGE_KEY) ?? "";
    expect(raw).not.toContain("token");
    expect(raw).not.toContain("Bearer");
    expect(raw).not.toContain("authorization");
  });

  it("filterRecentsByCaps filtra por capacidade do catálogo", () => {
    const items = pushRecentView({ viewId: "home", label: "Início" });
    // `home` exige `access` — interno vê, somente-DRE não.
    expect(
      filterRecentsByCaps(items, {
        access: true,
        manage: false,
        accessDre: false,
      }).length,
    ).toBe(1);
    expect(
      filterRecentsByCaps(items, {
        access: false,
        manage: false,
        accessDre: true,
      }).length,
    ).toBe(0);
  });
});
