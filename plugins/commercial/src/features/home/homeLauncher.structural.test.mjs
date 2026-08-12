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
    assert.match(catalog, /Propostas comerciais/);
  });

  it("HomePage usa stack vertical e SectionRouteCard", () => {
    const home = readSrc("features/home/HomePage.tsx");
    assert.match(home, /cm-home-stack/);
    assert.match(home, /CommercialSectionRouteCard/);
    assert.match(home, /CommercialCatalogSearchBar/);
    assert.match(home, /cm-home-queue-ok/);
    assert.match(home, /queueOkTitle/);
    assert.match(home, /cm-home-sections-grid/);
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
    assert.match(ui, /CommercialCommandPalette/);
  });
});
