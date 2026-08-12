#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const feature = join(root, "src/features/administration");
const content = join(root, "src/content/administration.ts");

describe("administration hub (Painel + SubNav + Carteiras)", () => {
  it("content tem labels das três abas", () => {
    const source = readFileSync(content, "utf8");
    assert.match(source, /navLabel: "Painel"/);
    assert.match(source, /navLabel: "Carteiras"/);
    assert.match(source, /navLabel: "Membros"/);
  });

  it("SubNav navega para as três views do hub", () => {
    const source = readFileSync(join(feature, "AdministrationSubNav.tsx"), "utf8");
    assert.match(source, /CommercialUnderlineNav/);
    assert.match(source, /administration_portfolios/);
    assert.match(source, /administration_members/);
    assert.match(source, /activeId=\{active\}/);
  });

  it("Painel carrega coverage + list e atalhos", () => {
    const source = readFileSync(join(feature, "AdministrationHomePage.tsx"), "utf8");
    assert.match(source, /listSellerPortfolios/);
    assert.match(source, /getSellerPortfoliosCoverageAudit/);
    assert.match(source, /AdministrationSubNav/);
    assert.match(source, /active="panel"/);
    assert.match(source, /openPortfolios/);
  });

  it("App roteia Painel, Carteiras e Membros", () => {
    const app = readFileSync(join(root, "src/App.tsx"), "utf8");
    assert.match(app, /AdministrationHomePage/);
    assert.match(app, /AdministrationMembersPage/);
    assert.match(app, /view === "administration"/);
    assert.match(app, /view === "administration_portfolios"/);
    assert.match(app, /view === "administration_members"/);
  });

  it("lista de carteiras embute SubNav do hub", () => {
    const page = readFileSync(
      join(root, "src/features/seller-portfolios/SellerPortfoliosPage.tsx"),
      "utf8",
    );
    assert.match(page, /AdministrationSubNav/);
    assert.match(page, /active="portfolios"/);
    assert.match(page, /navigatePluginView\("administration"/);
  });
});
