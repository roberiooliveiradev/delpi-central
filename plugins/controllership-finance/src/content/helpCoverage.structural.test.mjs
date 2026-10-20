#!/usr/bin/env node
/**
 * Ajuda contextual — todo hint referenciado em Home/Shell existe em CF_HELP.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "..");

function readSrc(relative) {
  return readFileSync(join(src, relative), "utf8");
}

const help = readSrc("content/helpTooltips.ts");

describe("ajuda contextual sincronizada", () => {
  it("todas as chaves usadas em Shell/Home existem no módulo de ajuda", () => {
    const used = [
      "shell.navHome",
      "home.overview",
      "home.events",
      "home.shortcuts",
      "home.search",
      "home.palette",
      "home.recents",
    ];
    const shell = readSrc("app/PluginShell.tsx");
    const page = readSrc("features/home/HomePage.tsx");
    for (const path of used) {
      const [group, key] = path.split(".");
      const referenced =
        shell.includes(`CF_HELP.${group}.${key}`) ||
        page.includes(`CF_HELP.${group}.${key}`) ||
        help.includes(`${key}:`);
      assert.ok(referenced, `hint não referenciado: CF_HELP.${path}`);
      assert.ok(
        help.includes(`${key}:`),
        `hint ausente em helpTooltips: CF_HELP.${path}`,
      );
    }
  });

  it("ajuda é conteúdo versionado — sem CMS/backend", () => {
    assert.match(help, /export const CF_HELP/);
    assert.doesNotMatch(help, /fetch\(|httpGet|api\//);
  });
});
