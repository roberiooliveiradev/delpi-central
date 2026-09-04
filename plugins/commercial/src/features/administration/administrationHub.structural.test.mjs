#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const feature = join(root, "src/features/administration");
const content = join(root, "src/content/administration.ts");

describe("administration hub (Painel · Carteiras · Equipe · Grupos · SLAs)", () => {
  it("content tem labels das cinco abas", () => {
    const source = readFileSync(content, "utf8");
    assert.match(source, /navLabel: "Painel"/);
    assert.match(source, /navLabel: "Carteiras"/);
    assert.match(source, /navLabel: "Equipe"/);
    assert.match(source, /navLabel: "Grupos"/);
    assert.match(source, /navLabel: "SLAs"/);
  });

  it("SubNav navega para as views do hub incluindo SLAs", () => {
    const source = readFileSync(join(feature, "AdministrationSubNav.tsx"), "utf8");
    assert.match(source, /CommercialUnderlineNav/);
    assert.match(source, /administration_portfolios/);
    assert.match(source, /administration_team/);
    assert.match(source, /administration_groups/);
    assert.match(source, /administration_slas/);
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
    assert.match(source, /administration_slas/);
    assert.match(source, /openTeam/);
    assert.match(source, /openGroups/);
    assert.match(source, /openSlas/);
  });

  it("Equipe consome team-roster + presença WS + diagrama grupos", () => {
    const source = readFileSync(join(feature, "AdministrationTeamPage.tsx"), "utf8");
    assert.match(source, /listTeamRoster/);
    assert.match(source, /useCommercialPresenceSync/);
    assert.match(source, /onlineUserIds/);
    assert.match(source, /navigateUserProfile/);
    assert.match(source, /active="team"/);
    assert.match(source, /CommercialDataTableSection/);
    assert.match(source, /CommercialSegmentToggle/);
    assert.match(source, /buildCommercialGroupsOrgFlowModel/);
    assert.match(source, /CommercialOrgMembershipFlow/);
    assert.match(source, /parseCommercialTeamView/);
    assert.match(source, /TaskUserChipAvatar/);
    assert.match(source, /withPersonAvatarSrc/);
    assert.match(source, /useUserProfilePhotoUrls/);
    assert.match(source, /key: "person"/);
    assert.match(source, /key: "online"/);
    assert.match(source, /key: "groups"/);
    assert.match(source, /key: "portfolios"/);
    assert.doesNotMatch(source, /key: "email"/);
    assert.doesNotMatch(source, /key: "actions"/);
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

  it("Grupos lista /groups, cria/renomeia/exclui e gerencia membros com picker+avatar", () => {
    const source = readFileSync(join(feature, "AdministrationGroupsPage.tsx"), "utf8");
    assert.match(source, /listCommercialGroups/);
    assert.match(source, /createCommercialGroup/);
    assert.match(source, /renameCommercialGroup/);
    assert.match(source, /deleteCommercialGroup/);
    assert.match(source, /addCommercialGroupMember/);
    assert.match(source, /removeCommercialGroupMember/);
    assert.match(source, /UserDirectoryPicker/);
    assert.match(source, /TaskUserChipAvatar/);
    assert.match(source, /active="groups"/);
    assert.match(source, /showCreateForm/);
    assert.match(source, /cm-administration-groups__create/);
    assert.match(source, /CommercialEmptyState/);
    assert.match(source, /closeCreateForm/);
    assert.match(source, /CommercialAvatarStack/);
    assert.match(source, /CommercialDataCardsGrid/);
    assert.match(source, /collapsible/);
    assert.match(source, /defaultOpen=\{false\}/);
    assert.match(source, /CommercialSegmentToggle/);
    assert.match(source, /parseCommercialTeamView/);
    assert.match(source, /CommercialOrgMembershipFlow/);
    assert.match(source, /buildCommercialGroupsOrgFlowModel/);
    assert.match(source, /withPersonAvatarSrc/);
    assert.match(source, /useUserProfilePhotoUrls/);
    const css = readFileSync(join(root, "src/index.css"), "utf8");
    assert.match(
      css,
      /\.cm-administration-groups \.cm-data-cards-grid[\s\S]*?auto-fit[\s\S]*?minmax\(min\(100%, 440px\), 1fr\)/,
    );
  });

  it("SLAs lista políticas, cria/edita e soft-desativa via API client", () => {
    const source = readFileSync(join(feature, "AdministrationSlasPage.tsx"), "utf8");
    assert.match(source, /listSlaPolicies/);
    assert.match(source, /includeInactive:\s*true/);
    assert.match(source, /createSlaPolicy/);
    assert.match(source, /updateSlaPolicy/);
    assert.match(source, /deactivateSlaPolicy/);
    assert.match(source, /active="slas"/);
    assert.match(source, /cm-administration-slas__form/);
    assert.match(source, /back=\{\{/);
    assert.match(source, /current=\{copy\.navLabel\}/);
    assert.match(source, /openCreate/);
    assert.match(source, /openEdit/);
    assert.match(source, /submitForm/);
    assert.match(source, /onDeactivate/);
    assert.match(source, /CommercialEmptyState/);
    assert.match(source, /CommercialDataTable/);
    const api = readFileSync(join(root, "src/api/slaPoliciesApi.ts"), "utf8");
    assert.match(api, /settings\/sla-policies/);
    assert.match(api, /include_inactive/);
    assert.match(api, /createSlaPolicy/);
    assert.match(api, /deactivateSlaPolicy/);
    const css = readFileSync(join(root, "src/index.css"), "utf8");
    assert.match(css, /\.cm-administration-slas__form/);
  });

  it("App roteia Painel, Carteiras, Equipe, Grupos e SLAs", () => {
    const app = readFileSync(join(root, "src/App.tsx"), "utf8");
    assert.match(app, /AdministrationHomePage/);
    assert.match(app, /AdministrationTeamPage/);
    assert.match(app, /AdministrationGroupsPage/);
    assert.match(app, /AdministrationSlasPage/);
    assert.match(app, /view === "administration"/);
    assert.match(app, /view === "administration_portfolios"/);
    assert.match(app, /view === "administration_team"/);
    assert.match(app, /view === "administration_groups"/);
    assert.match(app, /view === "administration_slas"/);
  });

  it("pluginRoutes resolve team/members/groups/slas", () => {
    const source = readFileSync(join(root, "src/app/pluginRoutes.ts"), "utf8");
    assert.match(source, /administration\/team/);
    assert.match(source, /administration\/members/);
    assert.match(source, /administration\/groups/);
    assert.match(source, /administration\/slas/);
    assert.match(source, /administration_team/);
    assert.match(source, /administration_groups/);
    assert.match(source, /administration_slas/);
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
