import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  collectSearchHits,
  filterRouteCatalog,
  resolveHomeContextualCta,
  resolveHubSections,
  scoreRouteMatch,
  tokenizeQuery,
  HUB_SECTIONS,
} from "./pluginRouteCatalog.ts";

const allCaps = {
  analytics: true,
  worklist: true,
  proposals: true,
  customers: true,
  admin: true,
};

describe("pluginRouteCatalog", () => {
  it("resolveHubSections omite seções sem rotas visíveis", () => {
    const sections = resolveHubSections({
      analytics: false,
      worklist: true,
      proposals: false,
      customers: false,
      admin: false,
    });
    assert.ok(sections.some((s) => s.id === "operations"));
    assert.ok(!sections.some((s) => s.id === "documents"));
  });

  it("filterRouteCatalog encontra propostas por keyword", () => {
    const sections = resolveHubSections(allCaps);
    const filtered = filterRouteCatalog(sections, "ady");
    assert.equal(filtered.length, 1);
    assert.equal(filtered[0]?.routes[0]?.id, "proposals");
  });

  it("collectSearchHits limita resultados", () => {
    const hits = collectSearchHits(resolveHubSections(allCaps), "pedido", 3);
    assert.ok(hits.length <= 3);
    assert.ok(hits.length > 0);
  });

  it("resolveHomeContextualCta prioriza pedidos em atraso", () => {
    const cta = resolveHomeContextualCta({
      ready: true,
      ordersLate: 2,
      tasksOverdue: 5,
      tasksToday: 1,
    });
    assert.equal(cta?.id, "orders_late");
    assert.equal(cta?.search, "?focus=late");
  });

  it("HUB_SECTIONS cobre as seções canônicas", () => {
    assert.deepEqual(
      HUB_SECTIONS.map((s) => s.id),
      ["operations", "management", "documents", "help", "administration"],
    );
  });

  it("inclui Sala de interação em Operação", () => {
    const sections = resolveHubSections(allCaps);
    const operations = sections.find((s) => s.id === "operations");
    assert.ok(operations?.routes.some((r) => r.id === "interaction_rooms"));
  });

  it("filterRouteCatalog encontra sala por keyword", () => {
    const sections = resolveHubSections(allCaps);
    const filtered = filterRouteCatalog(sections, "interação");
    assert.ok(
      filtered.some((s) => s.routes.some((r) => r.id === "interaction_rooms")),
    );
  });

  it("tokenizeQuery ignora partículas de 1 caractere", () => {
    assert.deepEqual(tokenizeQuery("gestão à vista"), ["gestao", "vista"]);
  });

  it("indicadores casa via description da seção Gestão à vista", () => {
    const sections = resolveHubSections(allCaps);
    const filtered = filterRouteCatalog(sections, "indicadores");
    assert.ok(
      filtered.some((s) => s.routes.some((r) => r.id === "overview")),
      "overview deve aparecer para «indicadores»",
    );
    const hits = collectSearchHits(sections, "indicadores", 8);
    assert.equal(hits[0]?.id, "overview");
  });

  it("gestão à vista casa pelo título da seção", () => {
    const sections = resolveHubSections(allCaps);
    const filtered = filterRouteCatalog(sections, "gestão à vista");
    assert.ok(filtered.some((s) => s.id === "management"));
    assert.ok(
      filtered
        .find((s) => s.id === "management")
        ?.routes.some((r) => r.id === "overview"),
    );
  });

  it("multi-token AND exige todos os tokens", () => {
    const sections = resolveHubSections(allCaps);
    const management = sections.find((s) => s.id === "management");
    const overview = management?.routes.find((r) => r.id === "overview");
    assert.ok(management && overview);
    assert.ok(scoreRouteMatch(management, overview, "visao geral") > 0);
    assert.equal(scoreRouteMatch(management, overview, "visao xyz"), 0);
  });

  it("collectSearchHits ranqueia label acima de description", () => {
    const sections = resolveHubSections(allCaps);
    const hits = collectSearchHits(sections, "oportunidades", 5);
    assert.equal(hits[0]?.id, "analytics_opportunities");
  });
});
