#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("commercial RBAC gates (sem aliases)", () => {
  it("scope não inventa team.view a partir de admin", () => {
    const source = readFileSync(join(src, "app/PortfolioScopeContext.tsx"), "utf8");
    assert.match(source, /canAccessMyPortfolio/);
    assert.doesNotMatch(source, /accounts_team_view \?\? teamScope/);
    assert.doesNotMatch(source, /team_scope \?\? admin/);
  });

  it("App e shell gateiam Minha Carteira e admin", () => {
    const app = readFileSync(join(src, "App.tsx"), "utf8");
    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    assert.match(app, /showCustomers=\{showCustomers\}/);
    assert.match(app, /canAccessMyPortfolio/);
    assert.match(app, /canManagePortfolios/);
    assert.match(shell, /resolveShellNavItems\(\{[\s\S]*?customers: showCustomers/);
    assert.match(shell, /admin: showAdmin/);
    assert.match(shell, /analytics: showAnalytics/);
    assert.match(shell, /worklist: showWorklist/);
  });

  it("navegação de topo tem as seis áreas da IA 2026", () => {
    const nav = readFileSync(join(src, "content/shellNav.ts"), "utf8");
    for (const [id, label] of [
      ["home", "Início"],
      ["overview", "Visão geral"],
      ["my_tasks", "Minhas tarefas"],
      ["open_orders", "Meus pedidos"],
      ["customers", "Minha Carteira"],
      ["administration", "Administração"],
    ]) {
      assert.match(nav, new RegExp(`id: "${id}", label: "${label}"`), id);
    }
    // Gestão, Propostas e Carteiras saíram do topo (launcher ou drill da Visão geral).
    assert.doesNotMatch(nav, /"Gestão"|"Propostas"|"Carteiras"/);
    assert.doesNotMatch(nav, /seller_portfolios|my_day/);

    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    assert.doesNotMatch(shell, /Gestão|AnalyticsSubNav|my_day/);
  });

  it("Visão geral só oferece drill de Equipe com canUseTeamScope", () => {
    const source = readFileSync(join(src, "features/overview/OverviewPage.tsx"), "utf8");
    assert.match(source, /canUseTeamScope/);
    assert.match(source, /analytics_otd/);
    assert.match(source, /analytics_opportunities/);
    assert.match(source, /canUseTeamScope[\s\S]*?analytics_team/);
  });

  it("SellerScopeFilter diferencia emptyLabel team vs minhas", () => {
    const source = readFileSync(
      join(src, "features/customers/components/SellerScopeFilter.tsx"),
      "utf8",
    );
    assert.match(source, /Todas as minhas carteiras/);
    assert.match(source, /Todas as carteiras/);
    assert.match(source, /teamScope/);
  });

  it("pedidos em aberto: CTA Abrir carteiras só com manage", () => {
    const source = readFileSync(join(src, "pages/OpenOrdersPageImpl.tsx"), "utf8");
    assert.match(source, /canOpenSellerPortfolios/);
    assert.match(source, /canManagePortfolios \|\| isAdmin/);
    assert.match(
      source,
      /canOpenSellerPortfolios \? \(\s*<ActionButton[\s\S]*?Abrir carteiras/,
    );
  });

  it("manifest sem texto de alias legado e team route canônica", () => {
    const manifest = readFileSync(join(root, "commercial.manifest.json"), "utf8");
    assert.doesNotMatch(manifest, /Alias legado|Alias:/);
    assert.match(manifest, /"path": "\/apps\/commercial\/analytics\/team"/);
    assert.match(
      manifest,
      /"path": "\/apps\/commercial\/analytics\/team"[\s\S]*?"permission": "commercial\.accounts\.team\.view"/,
    );
    assert.match(manifest, /"path": "\/apps\/commercial\/administration"/);
    assert.match(manifest, /"path": "\/apps\/commercial\/administration\/seller-portfolios"/);
    assert.match(manifest, /"path": "\/apps\/commercial\/administration\/team"/);
  });
});
