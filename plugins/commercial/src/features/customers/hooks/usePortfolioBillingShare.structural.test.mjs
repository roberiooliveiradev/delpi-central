#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("usePortfolioBillingShare", () => {
  it("expõe canView, formatSharePct e fetch getPortfolioBillingShare", () => {
    const source = readFileSync(join(here, "usePortfolioBillingShare.ts"), "utf8");
    assert.match(source, /export function canViewPortfolioBillingShare/);
    assert.match(source, /export function formatSharePct/);
    assert.match(source, /export function usePortfolioBillingShare/);
    assert.match(source, /getPortfolioBillingShare/);
  });

  it("card reexporta helpers e consome o hook", () => {
    const card = readFileSync(
      join(here, "../components/PortfolioBillingShareCard.tsx"),
      "utf8",
    );
    assert.match(card, /usePortfolioBillingShare/);
    assert.match(card, /export \{\s*canViewPortfolioBillingShare/);
  });
});
