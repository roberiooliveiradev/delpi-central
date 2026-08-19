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

  it("navegação de topo tem as sete áreas da IA 2026", () => {
    const nav = readFileSync(join(src, "content/shellNav.ts"), "utf8");
    for (const [id, label] of [
      ["home", "Início"],
      ["overview", "Visão geral"],
      ["interaction_rooms", "Sala de interação"],
      ["my_tasks", "Minhas tarefas"],
      ["open_orders", "Meus pedidos"],
      ["customers", "Minha Carteira"],
      ["administration", "Administração"],
    ]) {
      assert.match(nav, new RegExp(`id: "${id}", label: "${label}"`), id);
    }
    assert.match(
      nav,
      /id: "overview", label: "Visão geral"[\s\S]*?id: "interaction_rooms", label: "Sala de interação"/,
    );
    // Gestão / Propostas / Carteiras (admin) não são itens do topo.
    assert.doesNotMatch(nav, /id: "[^"]+", label: "(Gestão|Propostas|Carteiras)"/);
    assert.doesNotMatch(nav, /seller_portfolios|my_day/);

    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    assert.doesNotMatch(shell, /Gestão|AnalyticsSubNav|my_day/);
  });

  it("Visão geral é dashboard BI sem faixa Aprofundar nem prévia OV", () => {
    const source = readFileSync(join(src, "features/overview/OverviewPage.tsx"), "utf8");
    assert.match(source, /CommercialPageHero/);
    assert.match(source, /AnalyticsFilters/);
    assert.doesNotMatch(source, /cm-overview-drills|cm-page-header-row/);
    assert.doesNotMatch(source, /analytics_otd|analytics_opportunities|analytics_team/);
    assert.doesNotMatch(source, /getCommercialProposals|ov_table/);
  });

  it("SellerScopeFilter diferencia emptyLabel team vs minhas e analytics", () => {
    const source = readFileSync(
      join(src, "features/customers/components/SellerScopeFilter.tsx"),
      "utf8",
    );
    assert.match(source, /Todas as minhas carteiras/);
    assert.match(source, /Todas as carteiras/);
    assert.match(source, /ANALYTICS_PORTFOLIO_FILTER_EMPTY_LABEL/);
    assert.match(source, /Não filtrar/);
    assert.match(source, /teamScope/);
  });

  it("pedidos em aberto: CTA Abrir Administração só com manage", () => {
    const source = readFileSync(join(src, "pages/OpenOrdersPageImpl.tsx"), "utf8");
    assert.match(source, /canOpenSellerPortfolios/);
    assert.match(source, /canManagePortfolios \|\| isAdmin/);
    assert.match(
      source,
      /canOpenSellerPortfolios \? \(\s*<CommercialActionButton[\s\S]*?Abrir Administração/,
    );
    assert.match(source, /navigatePluginView\("administration"\)/);
    assert.doesNotMatch(source, /navigatePluginView\("seller_portfolios"\)/);
    assert.match(source, /cm-open-orders-page__chip-row/);
    assert.match(source, /scopeFilter=/);
    assert.doesNotMatch(source, /cm-open-orders-page__scope/);
  });

  it("manifest condensado: access/manage e team sob manage", () => {
    const manifest = readFileSync(join(root, "commercial.manifest.json"), "utf8");
    assert.doesNotMatch(manifest, /Alias legado|Alias:/);
    assert.match(manifest, /"code": "commercial\.access"/);
    assert.match(manifest, /"code": "commercial\.manage"/);
    assert.match(manifest, /"code": "commercial\.billing\.notify"/);
    assert.doesNotMatch(manifest, /commercial\.accounts\.view|commercial\.analytics\.view|seller-portfolios\.manage/);
    assert.match(
      manifest,
      /"path": "\/apps\/commercial\/analytics\/team"[\s\S]*?"permission": "commercial\.manage"/,
    );
    assert.match(manifest, /"path": "\/apps\/commercial\/administration"/);
    assert.match(manifest, /"path": "\/apps\/commercial\/administration\/seller-portfolios"/);
    assert.match(manifest, /"path": "\/apps\/commercial\/administration\/team"/);
  });

  it("Equipe redireciona para Administração", () => {
    const source = readFileSync(join(src, "features/analytics/AnalyticsTeamRedirect.tsx"), "utf8");
    assert.match(source, /navigatePluginView\("administration"/);
    assert.match(source, /replace: true/);
    const app = readFileSync(join(src, "App.tsx"), "utf8");
    assert.match(app, /AnalyticsTeamRedirect/);
    assert.doesNotMatch(app, /AnalyticsTeamPage/);
  });

  it("UserProfilePage desestrutura canManageFollowups e canViewWorklistTeam", () => {
    const source = readFileSync(join(src, "features/users/UserProfilePage.tsx"), "utf8");
    assert.match(source, /canManageFollowups,/);
    assert.match(source, /canViewWorklistTeam,/);
    assert.match(source, /canAssignTaskToProfile/);
  });

  it("CommercialMetricCard clicável não usa <button> (evita HelpTooltip aninhado)", () => {
    const source = readFileSync(join(src, "app/commercialUi.ts"), "utf8");
    const fn = source.slice(source.indexOf("export function CommercialMetricCard"));
    const body = fn.slice(0, fn.indexOf("/** KPI acionável"));
    assert.match(body, /role:\s*"button"/);
    assert.doesNotMatch(body, /createElement\(\s*"button"/);
  });
});
