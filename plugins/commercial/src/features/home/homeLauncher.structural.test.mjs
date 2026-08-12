#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

function readSrc(relativePath) {
  return readFileSync(join(src, relativePath), "utf8");
}

const LAUNCHER_CARD_IDS = [
  "overview",
  "my_tasks",
  "open_orders",
  "customers",
  "proposals",
  "analytics_otd",
  "analytics_opportunities",
  "analytics_team",
  "administration",
];

describe("Início launcher (IA 2026)", () => {
  it("catálogo de cards é orientado a conteúdo e capacidade", () => {
    const launcher = readSrc("content/homeLauncher.ts");
    assert.match(launcher, /export const HOME_LAUNCHER_CARDS/);
    assert.match(launcher, /export const HOME_LAUNCHER_CONTENT/);
    assert.match(launcher, /export function resolveHomeLauncherCards/);

    for (const id of LAUNCHER_CARD_IDS) {
      assert.match(launcher, new RegExp(`id: "${id}"`), id);
    }
    for (const capability of [
      "analytics",
      "worklist",
      "proposals",
      "customers",
      "team",
      "admin",
      "always",
    ]) {
      assert.match(launcher, new RegExp(`"${capability}"`), capability);
    }
    assert.match(launcher, /quickLinks\?:/);
  });

  it("prévia da worklist é uma chamada compartilhada", () => {
    const hook = readSrc("hooks/useWorklistPreview.ts");
    assert.match(hook, /export function useWorklistPreview/);
    assert.match(hook, /getMyWorklist/);
    assert.match(hook, /useCommercialWorklistSync/);
    // Ordem da prévia: atrasadas → hoje → depois
    assert.match(
      hook,
      /\["overdue"[\s\S]*?\["today"[\s\S]*?\["later"/,
    );
    assert.match(hook, /WORKLIST_PREVIEW_LIMIT = 5/);
    assert.equal((hook.match(/getMyWorklist\(/g) ?? []).length, 1);
  });

  it("Home consome launcher e prévia sem duplicar a fila", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.match(home, /useWorklistPreview/);
    assert.match(home, /resolveHomeLauncherCards/);
    assert.match(home, /HOME_LAUNCHER_CONTENT/);
    assert.match(home, /CommercialNavigationCard/);
    assert.doesNotMatch(home, /getMyWorklist/);
  });

  it("Home usa layout apps main + eventos side (C3)", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.match(home, /cm-home-columns/);
    assert.match(home, /cm-home-columns__main/);
    assert.match(home, /cm-home-columns__side/);
    assert.match(home, /cm-empty-quiet/);
    assert.match(home, /queueChips\.length > 0/);
  });

  it("Home é launcher: sem faixa BI nem tabela da equipe", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.doesNotMatch(home, /Seus n(?:ú|u)meros/);
    assert.doesNotMatch(home, /getHeadOfficeRolTargetPct|getClosingRate|getSalesOrderOtd/);
    assert.doesNotMatch(home, /DataTable|KpiCard/);
    assert.doesNotMatch(home, /cm-home-kpi-grid/);
  });

  it("Home navega pelos alvos da IA 2026 (sem carteiras direto)", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.doesNotMatch(home, /seller_portfolios/);
    assert.doesNotMatch(home, /"my_day"/);
    assert.match(home, /navigatePluginView\("my_tasks"/);

    const launcher = readSrc("content/homeLauncher.ts");
    assert.doesNotMatch(launcher, /seller_portfolios/);
    assert.match(launcher, /viewId: "administration"/);
    assert.match(launcher, /viewId: "overview"/);
  });

  it("alvos de navegação novos resolvem para uma rota existente", () => {
    const routes = readSrc("app/pluginRoutes.ts");
    assert.match(routes, /export type PluginNavigationTarget/);
    assert.match(routes, /"overview"/);
    assert.match(routes, /"my_tasks"/);
    assert.match(routes, /"administration"/);

    const navigation = readSrc("app/pluginNavigation.ts");
    assert.match(navigation, /view: PluginNavigationTarget/);
  });

  it("App passa capacidades de carteira e equipe para a Home", () => {
    const app = readSrc("App.tsx");
    assert.match(app, /showCustomers=\{canAccessMyPortfolio\}/);
    assert.match(app, /canUseTeamScope=\{canUseTeamScope\}/);
  });
});
