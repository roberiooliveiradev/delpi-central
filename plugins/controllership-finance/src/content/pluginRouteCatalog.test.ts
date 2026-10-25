import { describe, expect, it } from "vitest";

import {
  collectSearchHits,
  filterRouteCatalog,
  findHubRouteById,
  HUB_SECTIONS,
  resolveHubSections,
  scoreRouteMatch,
  tokenizeQuery,
} from "./pluginRouteCatalog";

describe("pluginRouteCatalog — apenas rotas implementadas", () => {
  it("cataloga somente as rotas implementadas no slice", () => {
    const routeIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.id));
    expect(routeIds).toEqual([
      "home",
      "closing-checklist",
      "financial-settlements",
      "closing-admin",
      "stock-inventory",
    ]);
    const viewIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.viewId));
    expect(new Set(viewIds)).toEqual(
      new Set([
        "home",
        "checklist",
        "checklist_admin",
        "financial_settlements",
        "stock_inventory",
      ]),
    );
  });

  it("não expõe rotas futuras (Visão geral, Sala, Tarefas, Admin, Ajuda, P1–P6)", () => {
    const allIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.id));
    for (const forbidden of [
      "overview",
      "interaction_rooms",
      "my_tasks",
      "administration",
      "help",
      "closing_center",
      "cockpit",
    ]) {
      expect(allIds).not.toContain(forbidden);
    }
  });

  it("resolveHubSections mantém seções com rotas always sem capabilities", () => {
    const sections = resolveHubSections({ manage: false });
    expect(sections.length).toBe(2);
    expect(sections[0].routes[0].id).toBe("home");
    expect(sections[1].routes[0].id).toBe("closing-checklist");
  });
});

describe("busca do catálogo", () => {
  it("tokenizeQuery ignora partículas curtas e acentos", () => {
    expect(tokenizeQuery("ínicio")).toEqual(["inicio"]);
    expect(tokenizeQuery("a")).toEqual([]);
  });

  it("scoreRouteMatch casa label e keywords", () => {
    const section = HUB_SECTIONS[0];
    const route = section.routes[0];
    expect(scoreRouteMatch(section, route, "inicio")).toBeGreaterThan(0);
    expect(scoreRouteMatch(section, route, "home")).toBeGreaterThan(0);
    expect(scoreRouteMatch(section, route, "fechamento")).toBe(0);
  });

  it("filterRouteCatalog filtra e retorna vazio sem match", () => {
    // «ini» casa «Início» e «admINIs tração» (label da rota admin).
    expect(filterRouteCatalog(HUB_SECTIONS, "ini").length).toBe(2);
    expect(filterRouteCatalog(HUB_SECTIONS, "xyz-inexistente").length).toBe(0);
    expect(filterRouteCatalog(HUB_SECTIONS, "").length).toBe(2);
    expect(filterRouteCatalog(HUB_SECTIONS, "baixas").length).toBe(1);
  });

  it("collectSearchHits retorna hit do Início", () => {
    const hits = collectSearchHits(HUB_SECTIONS, "inic");
    expect(hits.length).toBe(1);
    expect(hits[0].id).toBe("home");
    expect(hits[0].groupLabel).toBe("Portal");
  });

  it("collectSearchHits vazio sem query", () => {
    expect(collectSearchHits(HUB_SECTIONS, "")).toEqual([]);
  });

  it("findHubRouteById encontra por id", () => {
    expect(findHubRouteById(HUB_SECTIONS, "home")?.viewId).toBe("home");
    expect(findHubRouteById(HUB_SECTIONS, "nope")).toBeUndefined();
  });
});
