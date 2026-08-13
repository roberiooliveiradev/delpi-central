#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const feature = join(root, "src/features/administration");
const content = join(root, "src/content/administration.ts");

describe("administration hub (Painel · Carteiras · Equipe · Grupos)", () => {
  it("content tem labels das quatro abas", () => {
    const source = readFileSync(content, "utf8");
    assert.match(source, /navLabel: "Painel"/);
    assert.match(source, /navLabel: "Carteiras"/);
    assert.match(source, /navLabel: "Equipe"/);
    assert.match(source, /navLabel: "Grupos"/);
  });

  it("SubNav navega para as quatro views do hub", () => {
    const source = readFileSync(join(feature, "AdministrationSubNav.tsx"), "utf8");
    assert.match(source, /CommercialUnderlineNav/);
    assert.match(source, /administration_portfolios/);
    assert.match(source, /administration_team/);
    assert.match(source, /administration_groups/);
    assert.match(source, /activeId=\{active\}/);
  });

  it("Painel carrega coverage + list e atalhos Equipe/Grupos", () => {
    const source = readFileSync(join(feature, "AdministrationHomePage.tsx"), "utf8");
    assert.match(source, /listSellerPortfolios/);
    assert.match(source, /getSellerPortfoliosCoverageAudit/);
    assert.match(source, /AdministrationSubNav/);
    assert.match(source, /active="panel"/);
    assert.match(source, /administration_team/);
    assert.match(source, /administration_groups/);
    assert.match(source, /openTeam/);
    assert.match(source, /openGroups/);
  });

  it("Equipe consome team-roster + presença WS", () => {
    const source = readFileSync(join(feature, "AdministrationTeamPage.tsx"), "utf8");
    assert.match(source, /listTeamRoster/);
    assert.match(source, /useCommercialPresenceSync/);
    assert.match(source, /onlineUserIds/);
    assert.match(source, /navigateUserProfile/);
    assert.match(source, /active="team"/);
    assert.match(source, /CommercialDataTableSection/);
  });

  it("CommercialRealtimeProvider faz replay de presença no subscribe tardio", () => {
    const provider = readFileSync(
      join(root, "src/app/CommercialRealtimeProvider.tsx"),
      "utf8",
    );
    assert.match(provider, /subscribePresenceWithReplay/);
    assert.match(provider, /fanPresenceUpdated/);
    assert.match(provider, /lastPresenceRef/);
  });

  it("Grupos lista /groups, cria/exclui e gerencia membros com picker+avatar", () => {
    const source = readFileSync(join(feature, "AdministrationGroupsPage.tsx"), "utf8");
    assert.match(source, /listCommercialGroups/);
    assert.match(source, /createCommercialGroup/);
    assert.match(source, /deleteCommercialGroup/);
    assert.match(source, /addCommercialGroupMember/);
    assert.match(source, /removeCommercialGroupMember/);
    assert.match(source, /UserDirectoryPicker/);
    assert.match(source, /TaskUserChipAvatar/);
    assert.match(source, /active="groups"/);
    assert.match(source, /showCreateForm/);
    assert.match(source, /CommercialEmptyState/);
    assert.match(source, /closeCreateForm/);
  });

  it("App roteia Painel, Carteiras, Equipe e Grupos", () => {
    const app = readFileSync(join(root, "src/App.tsx"), "utf8");
    assert.match(app, /AdministrationHomePage/);
    assert.match(app, /AdministrationTeamPage/);
    assert.match(app, /AdministrationGroupsPage/);
    assert.match(app, /view === "administration"/);
    assert.match(app, /view === "administration_portfolios"/);
    assert.match(app, /view === "administration_team"/);
    assert.match(app, /view === "administration_groups"/);
  });

  it("pluginRoutes resolve team/members/groups", () => {
    const source = readFileSync(join(root, "src/app/pluginRoutes.ts"), "utf8");
    assert.match(source, /administration\/team/);
    assert.match(source, /administration\/members/);
    assert.match(source, /administration\/groups/);
    assert.match(source, /administration_team/);
    assert.match(source, /administration_groups/);
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
