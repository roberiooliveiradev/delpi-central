#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));

describe("PortfolioBillingShareCard", () => {
  it("usa hook + help CM_HELP sem api-delpi nem CSS de kit", () => {
    const source = readFileSync(join(here, "PortfolioBillingShareCard.tsx"), "utf8");
    assert.match(source, /usePortfolioBillingShare/);
    assert.match(source, /CM_HELP\.customers\.portfolioBillingShare/);
    assert.match(source, /CommercialDashboardKpiCard/);
    assert.doesNotMatch(source, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
    assert.doesNotMatch(source, /\.delpi-ui-/);
  });
});
