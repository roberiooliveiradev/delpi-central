#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("portfolio scope sync após portfolio.changed", () => {
  it("App religa reloadScope ao evento WS de carteira", () => {
    const app = readFileSync(join(src, "App.tsx"), "utf8");
    assert.match(app, /PortfolioScopeRealtimeSyncBridge/);
    assert.match(app, /useCommercialPortfolioSync/);
    assert.match(app, /reloadScope\(\)/);
  });

  it("CRUD de carteiras chama reloadScope localmente", () => {
    const list = readFileSync(
      join(src, "features/seller-portfolios/SellerPortfoliosPage.tsx"),
      "utf8",
    );
    const detail = readFileSync(
      join(src, "features/seller-portfolios/SellerPortfolioDetailPage.tsx"),
      "utf8",
    );
    assert.match(list, /reloadScope\(\)/);
    assert.match(detail, /reloadScope\(\)/);
    assert.match(detail, /handleAddMember[\s\S]*?reloadScope\(\)/);
  });

  it("Equipe Atualizar também recarrega o escopo de sellers", () => {
    const team = readFileSync(join(src, "features/analytics/AnalyticsTeamPage.tsx"), "utf8");
    assert.match(team, /reloadScope\(\)/);
    assert.match(team, /setReloadKey/);
  });
});
