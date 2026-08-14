#!/usr/bin/env node
import assert from "node:assert/strict";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const featureDirectory = dirname(fileURLToPath(import.meta.url));
const pluginRoot = join(featureDirectory, "../../..");

function filesUnder(directory, predicate = () => true) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    if (statSync(path).isDirectory()) {
      files.push(...filesUnder(path, predicate));
    } else if (predicate(path)) {
      files.push(path);
    }
  }
  return files;
}

describe("seller-portfolios kit-first", () => {
  const featureFiles = filesUnder(featureDirectory, (path) => /\.(?:ts|tsx)$/.test(path));
  const pageSource = readFileSync(join(featureDirectory, "SellerPortfoliosPage.tsx"), "utf8");
  const detailPageSource = readFileSync(
    join(featureDirectory, "SellerPortfolioDetailPage.tsx"),
    "utf8",
  );
  const orgSource = readFileSync(join(featureDirectory, "SellerPortfoliosOrgView.tsx"), "utf8");

  it("não usa button/input crus nem chrome cm-manage-panel", () => {
    for (const file of featureFiles) {
      const source = readFileSync(file, "utf8");
      assert.doesNotMatch(source, /<button\b/, file);
      assert.doesNotMatch(source, /<input\b/, file);
      assert.doesNotMatch(source, /cm-manage-panel/, file);
      assert.doesNotMatch(source, /cm-customer-chip-list/, file);
    }
  });

  it("lista full-page sem split layout nem painel «Selecione»", () => {
    assert.doesNotMatch(pageSource, /cm-portfolios-layout/);
    assert.doesNotMatch(pageSource, /Selecione uma carteira/);
    assert.doesNotMatch(pageSource, /selectedId/);
    assert.match(pageSource, /buildSellerPortfolioDetailPath/);
    assert.match(pageSource, /getSellerPortfoliosCoverageAudit/);
    assert.match(pageSource, /getSellerPortfoliosLoadSummary/);
    assert.match(pageSource, /SellerPortfolioBulkTransferWizard/);
    assert.match(pageSource, /exportOrgMatrixExcel|Exportar matriz/);
    assert.match(pageSource, /transferSellerCustomersBulk/);
    assert.match(pageSource, /filter:\s*"overlapping"|overlapping/);
    assert.match(pageSource, /filter:\s*"uncovered"|UncoveredCustomersPanel|filterUncovered/);
    assert.match(pageSource, /useCommercialPortfolioSync/);
    assert.match(detailPageSource, /SellerPortfolioDetail/);
    assert.match(detailPageSource, /SellerPortfolioAuditTimeline/);
    assert.match(detailPageSource, /useCommercialPortfolioSync/);
    assert.match(detailPageSource, /SellerPortfolioBulkTransferWizard/);
    assert.match(detailPageSource, /listSellerPortfolioAudit/);
    assert.match(detailPageSource, /addSellerPortfolioMember|setSellerPortfolioOwner/);
    assert.match(detailPageSource, /coverage_warning|readCoverageLinkWarning|notifyWarning/);
    assert.match(
      readFileSync(join(featureDirectory, "SellerPortfolioDetail.tsx"), "utf8"),
      /PORTFOLIO_MEMBERS_CONTENT|has_portal_access/,
    );
    assert.match(
      readFileSync(join(featureDirectory, "SellerPortfolioDetail.tsx"), "utf8"),
      /isOrphan|orphanBanner|emptyTitle/,
    );
    assert.match(
      readFileSync(join(pluginRoot, "src/content/portfolioMembersContent.ts"), "utf8"),
      /emptyTitle|orphanBanner|emptyCta/,
    );
    assert.match(orgSource, /Por carteira/);
    assert.match(orgSource, /Por pessoa/);
    assert.match(orgSource, /CommercialOrgMembershipFlow/);
    assert.match(orgSource, /buildSellerPortfoliosOrgFlowModel/);
    assert.match(orgSource, /fullscreenTitle|portalScopeClassName/);
    assert.doesNotMatch(orgSource, /cm-portfolios-org-tree/);
    // Troca Por carteira/Por pessoa atualiza nodes in-place — sem remount via ViewTransition+axis.
    assert.doesNotMatch(orgSource, /transitionKey=\{`org-\$\{axis\}/);
  });

  it("wizard de transferência em massa tem etapas origem→clientes→destino→confirmar", () => {
    const wizardSource = readFileSync(
      join(featureDirectory, "SellerPortfolioBulkTransferWizard.tsx"),
      "utf8",
    );
    assert.match(wizardSource, /PORTFOLIO_BULK_TRANSFER_CONTENT/);
    assert.match(wizardSource, /"source"/);
    assert.match(wizardSource, /"customers"/);
    assert.match(wizardSource, /"target"/);
    assert.match(wizardSource, /"confirm"/);
    assert.match(wizardSource, /CommercialHostDialog/);
    assert.doesNotMatch(wizardSource, /<button\b/);
  });

  it("modal Nova carteira é name-first (só nome; sem picker de usuários)", () => {
    const createSource = readFileSync(
      join(featureDirectory, "SellerPortfolioCreateDialog.tsx"),
      "utf8",
    );
    assert.match(createSource, /CommercialHostDialog/);
    assert.match(createSource, /Nome da carteira/);
    assert.match(createSource, /displayName/);
    assert.doesNotMatch(createSource, /UserDirectoryPicker/);
    assert.doesNotMatch(createSource, /userIds|user_ids/);
    assert.match(pageSource, /createSellerPortfolio\(\{\s*display_name:/);
    assert.match(pageSource, /onCreate=\{\(input\)\s*=>\s*void handleCreate\(input\)\}/);
  });

  it("carteira órfã: owner_user_id/user_id null não chama trim em null", () => {
    const detailPage = readFileSync(
      join(featureDirectory, "SellerPortfolioDetailPage.tsx"),
      "utf8",
    );
    assert.match(detailPage, /owner_user_id \?\? portfolio\.user_id \?\? ""\)\.trim\(\)/);
    assert.match(pageSource, /owner_user_id \?\? portfolio\.user_id \?\? ""\)\.trim\(\)/);
    assert.doesNotMatch(
      detailPage,
      /\(portfolio\.owner_user_id \?\? portfolio\.user_id\)\.trim\(\)/,
    );
  });

  it("timeline de auditoria usa kit Timeline, filtros e estados vazios", () => {
    const auditSource = readFileSync(
      join(featureDirectory, "SellerPortfolioAuditTimeline.tsx"),
      "utf8",
    );
    assert.match(auditSource, /CommercialActivityTimeline/);
    assert.match(auditSource, /SegmentToggle/);
    assert.match(auditSource, /toolbar=\{filterToolbar\}/);
    assert.match(auditSource, /PORTFOLIO_AUDIT_CONTENT/);
    assert.match(auditSource, /emptyMessage/);
    assert.match(auditSource, /CommercialLoadingCard/);
    assert.doesNotMatch(auditSource, /<button\b/);
  });

  it("não adiciona seletor do kit no CSS do MFE", () => {
    const cssFiles = filesUnder(join(pluginRoot, "src"), (path) => path.endsWith(".css"));
    for (const file of cssFiles) {
      assert.doesNotMatch(readFileSync(file, "utf8"), /\.delpi-ui-[\w-]+/, file);
    }
  });
});
