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

describe("pluginRouteCatalog — navegação consolidada (doc 112 §26)", () => {
  it("expõe Fechamento mensal como entrada principal + atalhos contextuais", () => {
    const routeIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.id));
    expect(routeIds).toEqual([
      "home",
      "profile",
      "monthly-closing",
      "monthly-closing-documents",
      "monthly-closing-reports",
      "closing-admin",
      "documents-admin",
      "catalogs-admin",
    ]);
    const viewIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.viewId));
    expect(new Set(viewIds)).toEqual(
      new Set([
        "home",
        "profile",
        "monthly_closing",
        "checklist_admin",
        "documents_admin",
        "catalogs_admin",
      ]),
    );
  });

  it("não expõe módulos técnicos como caminhos primários da Home", () => {
    const allIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.id));
    for (const removed of [
      "closing-checklist",
      "financial-settlements",
      "pendencies",
      "closing-packages",
      "closing-cockpit",
      "stock-inventory",
      "overview",
      "interaction_rooms",
      "administration",
      "help",
      "closing_center",
    ]) {
      expect(allIds).not.toContain(removed);
    }
  });

  it("atalhos contextuais apontam para abas do mesmo workspace", () => {
    const closing = HUB_SECTIONS.find((s) => s.id === "closing");
    const docs = closing?.routes.find((r) => r.id === "monthly-closing-documents");
    const reports = closing?.routes.find(
      (r) => r.id === "monthly-closing-reports",
    );
    expect(docs?.viewId).toBe("monthly_closing");
    expect(docs?.search).toBe("tab=documents");
    expect(reports?.viewId).toBe("monthly_closing");
    expect(reports?.search).toBe("tab=reports");
  });

  it("resolveHubSections mantém seções com rotas always sem capabilities", () => {
    const sections = resolveHubSections({ manage: false });
    expect(sections.length).toBe(2);
    expect(sections[0].routes[0].id).toBe("home");
    expect(sections[1].routes[0].id).toBe("monthly-closing");
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
