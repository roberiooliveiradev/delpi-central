#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

function readSrc(relative) {
  return readFileSync(join(src, relative), "utf8");
}

describe("user manual page", () => {
  it("conteúdo e página exportam o manual", () => {
    const content = readSrc("content/userManualContent.ts");
    assert.match(content, /export const USER_MANUAL_CONTENT/);
    assert.match(content, /pageTitle: \"Manual do usuário\"/);
    assert.match(content, /USER_MANUAL_TERM_CATALOG/);
    assert.match(content, /Catálogo de termos/);
    assert.match(content, /Minha Carteira → ABC/);
    assert.match(content, /painel ABC/);
    assert.match(content, /Administração → SLAs/);
    assert.match(content, /Onde configuro os SLAs/);
    const catalog = readSrc("content/userManualTermCatalog.ts");
    assert.match(catalog, /export const USER_MANUAL_TERM_CATALOG/);
    assert.match(catalog, /term: \"EXW\"/);
    assert.match(catalog, /term: \"FOB\"/);
    assert.match(catalog, /term: \"CIF\"/);
    assert.match(catalog, /applies:/);
    assert.match(catalog, /Minha Carteira → ABC/);
    const page = readSrc("features/help/UserManualPage.tsx");
    assert.match(page, /USER_MANUAL_CONTENT/);
    assert.match(page, /glossaryGroups/);
    assert.match(page, /Onde aparece/);
    assert.match(page, /UserManualLinkedText/);
    assert.match(page, /cm-user-manual__layout/);
    const links = readSrc("content/userManualToolLinks.ts");
    assert.match(links, /MANUAL_TOOL_TARGETS/);
    assert.match(links, /splitManualTextWithToolLinks/);
    assert.match(links, /Minha Carteira → ABC/);
    assert.match(links, /\?panel=abc/);
    assert.match(links, /Administração → SLAs/);
    assert.match(links, /administration_slas/);
  });

  it("App e manifesto expõem /help", () => {
    const app = readSrc("App.tsx");
    assert.match(app, /UserManualPage/);
    assert.match(app, /view === \"help\"/);
    const routes = readSrc("app/pluginRoutes.ts");
    assert.match(routes, /relativePath === \"help\"/);
    assert.match(routes, /help: \"help\"/);
    const manifest = readFileSync(
      join(src, "..", "commercial.manifest.json"),
      "utf8",
    );
    assert.match(manifest, /\/apps\/commercial\/help/);
  });
});
