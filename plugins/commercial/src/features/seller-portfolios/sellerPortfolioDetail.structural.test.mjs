#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const detail = readFileSync(join(here, "SellerPortfolioDetail.tsx"), "utf8");
const page = readFileSync(join(here, "SellerPortfolioDetailPage.tsx"), "utf8");

describe("SellerPortfolioDetail UX", () => {
  it("usa CustomerSearchPicker com avatares e vincular selecionados", () => {
    assert.match(detail, /CustomerSearchPicker/);
    assert.match(detail, /CustomerAvatar/);
    assert.match(detail, /onAddCustomers/);
    assert.match(detail, /Vincular selecionados/);
    assert.match(detail, /maxSelected=\{20\}/);
    assert.doesNotMatch(detail, /useActiveCustomerSearch/);
    assert.doesNotMatch(detail, /apiDelpiUrl|API_DELPI|\/apps\/api-delpi/);
  });

  it("page faz vínculo em lote sequencial", () => {
    assert.match(page, /handleAddCustomers/);
    assert.match(page, /linkingCustomers/);
    assert.match(page, /Vínculo parcial|vinculado\(s\)/);
  });
});
