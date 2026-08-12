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
    assert.match(pageSource, /filter:\s*"overlapping"|overlapping/);
    assert.match(detailPageSource, /SellerPortfolioDetail/);
    assert.match(detailPageSource, /addSellerPortfolioMember|setSellerPortfolioOwner/);
    assert.match(detailPageSource, /coverage_warning|readCoverageLinkWarning|notifyWarning/);
    assert.match(orgSource, /Por carteira/);
    assert.match(orgSource, /Por pessoa/);
    assert.match(orgSource, /formatPortfolioLoadSnippet|cm-portfolios-org-tree__load/);
  });

  it("não adiciona seletor do kit no CSS do MFE", () => {
    const cssFiles = filesUnder(join(pluginRoot, "src"), (path) => path.endsWith(".css"));
    for (const file of cssFiles) {
      assert.doesNotMatch(readFileSync(file, "utf8"), /\.delpi-ui-[\w-]+/, file);
    }
  });
});
