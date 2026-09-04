#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  DEFAULT_OPPORTUNITIES_VIEW,
  applyOpportunitiesViewToSearchParams,
  normalizeOpportunitiesView,
  parseOpportunitiesView,
} from "./opportunitiesViewDeepLink.ts";

describe("opportunitiesViewDeepLink", () => {
  it("defaulta opportunity quando view ausente ou inválida", () => {
    assert.equal(parseOpportunitiesView(""), DEFAULT_OPPORTUNITIES_VIEW);
    assert.equal(parseOpportunitiesView("?search=acme"), DEFAULT_OPPORTUNITIES_VIEW);
    assert.equal(parseOpportunitiesView("?view=nope"), DEFAULT_OPPORTUNITIES_VIEW);
    assert.equal(normalizeOpportunitiesView(null), "opportunity");
    assert.equal(normalizeOpportunitiesView("  COLLABORATOR  "), "collaborator");
  });

  it("parseia collaborator e opportunity", () => {
    assert.equal(parseOpportunitiesView("?view=collaborator"), "collaborator");
    assert.equal(parseOpportunitiesView("?view=opportunity&search=x"), "opportunity");
  });

  it("omite view na URL quando default opportunity", () => {
    const params = new URLSearchParams("search=acme&view=collaborator");
    applyOpportunitiesViewToSearchParams(params, "opportunity");
    assert.equal(params.get("view"), null);
    assert.equal(params.get("search"), "acme");
  });

  it("grava view=collaborator e preserva outros params", () => {
    const params = new URLSearchParams("search=acme");
    applyOpportunitiesViewToSearchParams(params, "collaborator");
    assert.equal(params.get("view"), "collaborator");
    assert.equal(params.get("search"), "acme");
  });
});
