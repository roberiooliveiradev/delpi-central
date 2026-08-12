import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  collectSearchHits,
  filterRouteCatalog,
  resolveHomeContextualCta,
  resolveHubSections,
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
    const hits = collectSearchHits(resolveHubSections(allCaps), "a", 3);
    assert.ok(hits.length <= 3);
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

  it("HUB_SECTIONS cobre as quatro seções canônicas", () => {
    assert.deepEqual(
      HUB_SECTIONS.map((s) => s.id),
      ["operations", "management", "documents", "administration"],
    );
  });
});
