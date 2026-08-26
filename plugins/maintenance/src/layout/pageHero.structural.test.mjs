#!/usr/bin/env node
/**
 * PageHero — páginas do MFE Manutenção usam MaintenancePageHero / MaintenanceMiniAplicadoresHero.
 */
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const pagesDir = join(here, "../ui/pages");

function readPage(name) {
  return readFileSync(join(pagesDir, name), "utf8");
}

function listPageFiles() {
  return readdirSync(pagesDir).filter((name) => name.endsWith(".tsx"));
}

describe("Maintenance page hero — ui/pages", () => {
  it("zero imports de PageHeader ou MiniAplicadoresPageHeader", () => {
    for (const file of listPageFiles()) {
      const source = readPage(file);
      assert.doesNotMatch(source, /from\s+["'][^"']*PageHeader["']/);
      assert.doesNotMatch(source, /from\s+["'][^"']*MiniAplicadoresPageHeader["']/);
      assert.doesNotMatch(source, /<PageHeader\b/);
      assert.doesNotMatch(source, /<MiniAplicadoresPageHeader\b/);
    }
  });

  it("cada página usa MaintenancePageHero ou MaintenanceMiniAplicadoresHero", () => {
    for (const file of listPageFiles()) {
      const source = readPage(file);
      const usesHero =
        source.includes("<MaintenancePageHero") ||
        source.includes("<MaintenanceMiniAplicadoresHero");
      assert.ok(usesHero, `${file}: deve usar MaintenancePageHero ou MaintenanceMiniAplicadoresHero`);
    }
  });

  it("hero mini-aplicadores sem nav embutida (sub-abas na TopBar)", () => {
    const heroSource = readFileSync(join(here, "../components/MaintenanceMiniAplicadoresHero.tsx"), "utf8");
    assert.doesNotMatch(heroSource, /MiniAplicadoresNav/);
    assert.doesNotMatch(heroSource, /<MaintenancePageHero[\s\S]*>[\s\S]*<nav/);
  });
});
