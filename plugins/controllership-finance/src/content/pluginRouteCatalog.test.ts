import { describe, expect, it } from "vitest";

import {
  collectSearchHits,
  filterRouteCatalog,
  findHubRouteById,
  HUB_SECTIONS,
  LNF_APP_HREF,
  resolveHubSections,
  scoreRouteMatch,
  tokenizeQuery,
} from "./pluginRouteCatalog";

describe("pluginRouteCatalog — home-hub H3 (padrão Portais)", () => {
  it("expõe cards alvo: Fechamento, Notas fiscais, Administração, DRE", () => {
    expect(HUB_SECTIONS.map((s) => s.id)).toEqual([
      "closing",
      "notas_fiscais",
      "administration",
      "closing_dre",
    ]);
    const routeIds = HUB_SECTIONS.flatMap((s) => s.routes.map((r) => r.id));
    expect(routeIds).toEqual([
      "monthly-closing",
      "monthly-closing-documents",
      "monthly-closing-reports",
      "entry-audit",
      "lnf-app",
      "closing-admin",
      "documents-admin",
      "catalogs-admin",
      "dre-monthly-closing",
    ]);
    expect(routeIds).not.toContain("home");
    expect(routeIds).not.toContain("profile");
  });

  it("link LNF é externo com href canônico e cap lnfAccess", () => {
    const lnf = findHubRouteById(HUB_SECTIONS, "lnf-app");
    expect(lnf?.kind).toBe("external");
    expect(lnf?.href).toBe(LNF_APP_HREF);
    expect(lnf?.requiredCap).toBe("lnfAccess");
    expect(lnf?.viewId).toBeUndefined();
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
      "help",
      "closing_center",
      "home",
      "profile",
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

  it("resolveHubSections projeta as seções por capability (RW03 + H3)", () => {
    const internal = resolveHubSections({
      access: true,
      manage: false,
      accessDre: false,
      lnfAccess: false,
    });
    expect(internal.map((s) => s.id)).toEqual(["closing", "notas_fiscais"]);
    expect(internal[0].routes.map((r) => r.id)).toEqual([
      "monthly-closing",
      "monthly-closing-documents",
      "monthly-closing-reports",
    ]);
    expect(internal[1].routes.map((r) => r.id)).toEqual(["entry-audit"]);

    const withLnf = resolveHubSections({
      access: true,
      manage: false,
      accessDre: false,
      lnfAccess: true,
    });
    expect(
      withLnf.find((s) => s.id === "notas_fiscais")?.routes.map((r) => r.id),
    ).toEqual(["entry-audit", "lnf-app"]);

    const dre = resolveHubSections({
      access: false,
      manage: false,
      accessDre: true,
      lnfAccess: false,
    });
    expect(dre.length).toBe(1);
    expect(dre[0].id).toBe("closing_dre");
    expect(dre[0].routes.map((r) => r.id)).toEqual(["dre-monthly-closing"]);

    expect(
      resolveHubSections({
        access: false,
        manage: false,
        accessDre: false,
        lnfAccess: false,
      }),
    ).toEqual([]);

    const manageOnly = resolveHubSections({
      access: false,
      manage: true,
      accessDre: false,
      lnfAccess: false,
    });
    expect(manageOnly.map((s) => s.id)).toEqual(["administration"]);
    expect(manageOnly.flatMap((s) => s.routes.map((r) => r.id))).toEqual([
      "closing-admin",
      "documents-admin",
      "catalogs-admin",
    ]);
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
    expect(scoreRouteMatch(section, route, "fechamento")).toBeGreaterThan(0);
    expect(scoreRouteMatch(section, route, "inicio")).toBe(0);
  });

  it("filterRouteCatalog filtra e retorna vazio sem match", () => {
    expect(filterRouteCatalog(HUB_SECTIONS, "fechamento").length).toBeGreaterThan(0);
    expect(filterRouteCatalog(HUB_SECTIONS, "xyz-inexistente").length).toBe(0);
    expect(filterRouteCatalog(HUB_SECTIONS, "").length).toBe(4);
    expect(filterRouteCatalog(HUB_SECTIONS, "baixas").length).toBe(1);
  });

  it("collectSearchHits não indexa Início (D7)", () => {
    expect(collectSearchHits(HUB_SECTIONS, "inic")).toEqual([]);
    const hits = collectSearchHits(HUB_SECTIONS, "auditoria");
    expect(hits[0]?.id).toBe("entry-audit");
    expect(hits[0]?.groupLabel).toBe("Notas fiscais");
  });

  it("collectSearchHits vazio sem query", () => {
    expect(collectSearchHits(HUB_SECTIONS, "")).toEqual([]);
  });

  it("findHubRouteById encontra por id", () => {
    expect(findHubRouteById(HUB_SECTIONS, "entry-audit")?.viewId).toBe(
      "entry_audit",
    );
    expect(findHubRouteById(HUB_SECTIONS, "nope")).toBeUndefined();
  });
});
