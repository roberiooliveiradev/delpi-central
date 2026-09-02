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
    const page = readSrc("features/help/UserManualPage.tsx");
    assert.match(page, /USER_MANUAL_CONTENT/);
    assert.match(page, /cm-user-manual__layout/);
    assert.match(page, /cm-user-manual__main/);
    assert.match(page, /cm-user-manual__concept-card/);
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
