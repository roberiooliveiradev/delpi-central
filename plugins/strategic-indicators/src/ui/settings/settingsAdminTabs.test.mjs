#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  parseCatalogAdminView,
  parseSettingsAdminTab,
} from "./settingsAdminTabs.ts";

describe("settingsAdminTabs", () => {
  it("resolve aliases legados para abas canônicas", () => {
    assert.equal(parseSettingsAdminTab(null), "overview");
    assert.equal(parseSettingsAdminTab("painel"), "overview");
    assert.equal(parseSettingsAdminTab("departments"), "catalog");
    assert.equal(parseSettingsAdminTab("global"), "system");
    assert.equal(parseSettingsAdminTab("audit"), "system");
    assert.equal(parseCatalogAdminView("validacao"), "validation");
    assert.equal(parseCatalogAdminView("estrutura"), "structure");
  });
});
