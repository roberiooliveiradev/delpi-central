#!/usr/bin/env node
/**
 * Home honesta — IMP-MFE-HOME.
 * Sem KPIs, tarefas, blockers ou competência fabricados; deep link ?q=;
 * catálogo só com rotas implementadas; recents sem dados sensíveis.
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
  it("não fabrica métricas — hero usa «—» (indisponível), não valores", () => {
    const shell = readSrc("app/PluginShell.tsx");
    assert.match(shell, /highlightsUnavailable/);
    // Nenhum fetch de KPI/tasks/blockers — fontes ainda não existem.
    assert.doesNotMatch(shell, /getMyTask|getBlocker|getActiveCompetence|getKpi/i);
    assert.doesNotMatch(shell, /\b\d+\s*(na fila|em atraso|tarefas?)\b/);
  });

  it("HomePage não chama endpoints de dados operacionais", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.doesNotMatch(page, /getOpenOrders|getMyWorklist|listInteractionRooms|summary|atrasos/i);
    assert.doesNotMatch(page, /\bvalor\b|\bR\$|formatCurrency/);
  });

  it("catálogo publica somente viewIds implementados", () => {
    const catalog = readSrc("content/pluginRouteCatalog.ts");
    const viewIds = [...catalog.matchAll(/viewId: "([^"]+)"/g)].map((m) => m[1]);
    assert.deepEqual(
      new Set(viewIds),
      new Set([
        "home",
        "checklist",
        "checklist_admin",
        "financial_settlements",
        "pendencies",
        "stock_inventory",
      ]),
    );
    assert.doesNotMatch(catalog, /my_tasks|overview|interaction_rooms|administration|help|open_orders/);
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
    // Sem token/credencial persistida.
    assert.doesNotMatch(recents, /accessToken|Bearer\s|authorization|password|cpf/i);
  });

  it("favoritos não existem nesta entrega (D3=A DEFERRED)", () => {
    const page = readSrc("features/home/HomePage.tsx");
    const catalog = readSrc("content/pluginRouteCatalog.ts");
    for (const code of [page, catalog]) {
      assert.doesNotMatch(code, /\bfavorites?\b|\bfavoritos?\b|\bpinLabel\b|\bonPinClick\b|\bStar\b/i);
    }
  });

  it("eventos renderizam estado indisponível honesto — não empty positivo", () => {
    const page = readSrc("features/home/HomePage.tsx");
    assert.match(page, /omitWhenEmpty=\{false\}/);
    assert.match(page, /EVENTS\.unavailable/);
    const content = readSrc("content/pluginRouteCatalog.ts");
    assert.match(content, /indisponíveis nesta versão/i);
  });
});
