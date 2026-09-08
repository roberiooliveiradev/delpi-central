#!/usr/bin/env node
/**
 * Hub Início — stack seções + busca (não colunas legacy).
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

describe("home hub stack", () => {
  it("catálogo canônico exporta seções e filtros", () => {
    const catalog = readSrc("content/pluginRouteCatalog.ts");
    assert.match(catalog, /export const HUB_SECTIONS/);
    assert.match(catalog, /export function filterRouteCatalog/);
    assert.match(catalog, /export function collectSearchHits/);
    assert.match(catalog, /create_task/);
    assert.match(catalog, /orders_billable/);
    assert.match(catalog, /orders_postponed/);
    assert.match(catalog, /orders_ready_board/);
    assert.match(catalog, /id: \"help\"/);
    assert.match(catalog, /user_manual/);
    assert.match(catalog, /viewId: \"help\"/);
  });

  it("HomePage usa stack vertical e SectionRouteCard", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.match(home, /cm-home-stack/);
    assert.match(home, /CommercialSectionRouteCard/);
    assert.match(home, /CommercialCatalogSearchBar/);
    assert.match(home, /CommercialHubChipRow/);
    assert.match(home, /CommercialRouteChip/);
    assert.match(home, /leadingIcon/);
    assert.match(home, /cm-home-queue-ok/);
    assert.match(home, /queueOkTitle/);
    assert.match(home, /cm-home-sections-grid/);
    assert.match(home, /getHomeFavorites|putHomeFavorites|refreshHomeFavorites/);
    assert.match(home, /onPinClick/);
    assert.match(home, /buildOpenOrdersHorizonListHref/);
    assert.match(home, /month-deliveries/);
    assert.doesNotMatch(home, /dashboard-production|tv-dashboard/);
    assert.doesNotMatch(home, /window\.location\.assign/);
    assert.doesNotMatch(home, /kind === ["']create["']/);
    assert.doesNotMatch(home, /cm-home-columns/);
    assert.doesNotMatch(home, /HOME_LAUNCHER_CONTENT/);
    assert.doesNotMatch(home, /cm-home-grid--primary/);
  });

  it("catálogo inclui atalho Nova tarefa create", () => {
    const catalog = readSrc("content/pluginRouteCatalog.ts");
    assert.match(catalog, /id: "create_task"/);
    assert.match(catalog, /kind: "create"/);
    assert.match(catalog, /\?createTask=1/);
  });

  it("CSS define stack e grid de seções", () => {
    const css = readSrc("index.css");
    assert.match(css, /\.cm-home-stack\b/);
    assert.match(css, /\.cm-home-sections-grid\b/);
    assert.match(css, /\.cm-home-queue-ok\b/);
    assert.doesNotMatch(css, /\.cm-home-columns\b/);
  });

  it("bindings kit no commercialUi", () => {
    const ui = readSrc("app/commercialUi.ts");
    assert.match(ui, /CommercialSectionRouteCard/);
    assert.match(ui, /CommercialCatalogSearchBar/);
    assert.match(ui, /CommercialHubChipRow/);
    assert.match(ui, /CommercialRouteChip/);
    assert.match(ui, /CommercialCommandPalette/);
    assert.match(ui, /CommercialTopBarSearchTrigger/);
    assert.match(ui, /createDashboardTopBarSearchTrigger/);
  });

  it("PluginShell abre CommandPalette com Ctrl/Cmd+K", () => {
    const shell = readSrc("app/PluginShell.tsx");
    assert.match(shell, /CommercialCommandPalette/);
    assert.match(shell, /metaKey \|\| event\.ctrlKey/);
    assert.match(shell, /HUB_CONTENT\.palette/);
    assert.match(shell, /ShellTopBarSecondary/);
    assert.match(shell, /onOpenPalette=\{\(\) => setPaletteOpen\(true\)\}/);
    assert.match(shell, /anchorRef=\{searchTriggerRef\}/);
    assert.match(shell, /searchTriggerRef/);
  });

  it("secondary da TopBar compõe busca kit + favoritos", () => {
    const secondary = readSrc("app/ShellTopBarSecondary.tsx");
    const shellCss = readSrc("styles/shell.css");
    const help = readSrc("content/helpTooltips.ts");
    assert.match(secondary, /CommercialTopBarSearchTrigger/);
    assert.match(secondary, /ShellFavoritesStrip/);
    assert.match(secondary, /searchTriggerRef/);
    assert.match(secondary, /SHELL_NAV_CONTENT\.searchLabel/);
    assert.match(secondary, /onOpen=\{onOpenPalette\}/);
    assert.match(shellCss, /\.cm-shell-secondary/);
    assert.doesNotMatch(shellCss, /\.delpi-ui-topbar-search/);
    assert.match(help, /botão Buscar da barra superior/);
    assert.match(help, /popover ancorado/);
  });
});
