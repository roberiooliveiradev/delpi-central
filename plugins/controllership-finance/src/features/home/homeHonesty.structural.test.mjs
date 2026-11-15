#!/usr/bin/env node
/**
 * Home honesta — IMP-MFE-HOME + UI review H1.
 * Highlights vêm de leituras reais (competências / última auditoria);
 * sem KPI fabricado; deep link ?q=; catálogo só com rotas implementadas.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

function readSrc(relative) {
  return readFileSync(join(src, relative), "utf8");
}

describe("home honesty", () => {
  it("hero carrega highlights reais (nunca traço estático)", () => {
    const shell = readSrc("app/PluginShell.tsx");
    assert.match(shell, /loadHomeHeroHighlights/);
    assert.doesNotMatch(shell, /highlightsUnavailable/);
    assert.doesNotMatch(shell, /\b\d+\s*(na fila|em atraso|tarefas?)\b/);
  });

  it("HomePage não chama endpoints de dados operacionais de fechamento", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.doesNotMatch(page, /getOpenOrders|getMyWorklist|listInteractionRooms|atrasos/i);
    assert.doesNotMatch(page, /\bvalor\b|\bR\$|formatCurrency/);
  });

  it("recents usam ícone da rota (H2)", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.match(page, /hubRouteIcon/);
    assert.doesNotMatch(
      page,
      /CfRecentAccessStrip[\s\S]*icon:\s*SECTION_ICONS\.closing/,
    );
  });

  it("catálogo publica somente viewIds implementados", () => {
    const catalog = readSrc("content/pluginRouteCatalog.ts");
    const viewIds = [...catalog.matchAll(/viewId: "([^"]+)"/g)].map((m) => m[1]);
    assert.deepEqual(
      new Set(viewIds),
      new Set([
        "monthly_closing",
        "entry_audit",
        "checklist_admin",
        "documents_admin",
        "catalogs_admin",
        "received_documents",
      ]),
    );
    assert.doesNotMatch(catalog, /overview|interaction_rooms|open_orders/);
  });

  it("busca ?q= está ligada (read + write na URL)", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.match(page, /readHomeSearchQuery/);
    assert.match(page, /writeHomeSearchQuery/);
    const query = readSrc("features/home/homeSearchQuery.ts");
    assert.match(query, /params\.get\("q"\)/);
    assert.match(query, /searchParams\.set\("q"/);
  });

  it("recents são locais, limitados, deduplicados e sem dados sensíveis", () => {
    const recents = readSrc("features/home/homeRecentViews.ts");
    assert.match(recents, /MAX_RECENTS = 5/);
    assert.match(recents, /dedupeKey/);
    assert.match(recents, /localStorage/);
    assert.doesNotMatch(recents, /accessToken|Bearer\s|authorization|password|cpf/i);
  });

  it("link LNF externo expõe tooltip de app externo (H3)", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.match(page, /LNF_EXTERNAL_TOOLTIP/);
    assert.match(page, /hubRouteIcon/);
  });

  it("eventos renderizam estado indisponível honesto — não empty positivo", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.match(page, /omitWhenEmpty=\{false\}/);
    assert.match(page, /EVENTS\.unavailable/);
    const content = readSrc("content/pluginRouteCatalog.ts");
    assert.match(content, /indisponíveis nesta versão/i);
  });
});
