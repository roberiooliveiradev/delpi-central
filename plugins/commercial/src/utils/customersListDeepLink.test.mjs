#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCustomersListPath,
  buildCustomersListSearch,
  isCustomersListPathname,
  parseCustomersListDeepLink,
  sanitizeCustomersListSearch,
} from "./customersListDeepLink.ts";
import { updateCustomersListState } from "../features/customers/hooks/useCustomersListState.ts";

const TEAM_ACCESS = {
  allowSellerId: true,
  validSellerIds: ["seller-1", "seller-2"],
};

describe("customersListDeepLink", () => {
  it("parseia somente o estado reconhecido", () => {
    assert.deepEqual(
      parseCustomersListDeepLink(
        "?q=%20Acme%20&focus=growth&seller_id=seller-2&sort=billed12m&dir=desc&page=3&external=https://example.com",
        TEAM_ACCESS,
      ),
      {
        q: "Acme",
        focus: "growth",
        sellerId: "seller-2",
        sort: "billed12m",
        dir: "desc",
        page: 3,
      },
    );
  });

  it("normaliza foco e vendedor inválidos", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?q=%20%20&focus=late&seller_id=unknown", TEAM_ACCESS),
      {
        q: "",
        focus: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
      },
    );
    assert.equal(
      sanitizeCustomersListSearch(
        "?focus=no_sale_60&seller_id=seller-1&redirect=https://example.com",
        TEAM_ACCESS,
      ),
      "?focus=no_sale_60&seller_id=seller-1",
    );
  });

  it("remove seller_id sem permissão de equipe", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?seller_id=seller-1", {
        allowSellerId: false,
        validSellerIds: ["seller-1"],
      }),
      {
        q: "",
        focus: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
      },
    );
  });

  it("mantém roundtrip canônico e rota interna", () => {
    const state = {
      q: "Metalúrgica A",
      focus: "attention",
      sellerId: "seller-1",
      sort: "lastPurchaseDate",
      dir: "desc",
      page: 4,
    };
    const search = buildCustomersListSearch(state, TEAM_ACCESS);
    assert.equal(search, "?q=Metal%C3%BArgica+A&focus=attention&seller_id=seller-1&sort=lastPurchaseDate&dir=desc&page=4");
    assert.deepEqual(parseCustomersListDeepLink(search, TEAM_ACCESS), state);
    assert.equal(
      buildCustomersListPath("https://malicioso.example", state, TEAM_ACCESS),
      "/apps/commercial/customers?q=Metal%C3%BArgica+A&focus=attention&seller_id=seller-1&sort=lastPurchaseDate&dir=desc&page=4",
    );
  });

  it("aplica defaults e remove toda query fora da allowlist", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?focus=x&sort=__proto__&dir=up&page=-2&unknown=1", TEAM_ACCESS),
      { q: "", focus: "all", sellerId: null, sort: "attention", dir: "asc", page: 1 },
    );
    assert.equal(
      sanitizeCustomersListSearch("?q=ACME&focus=all&sort=attention&dir=asc&page=1&unknown=1", TEAM_ACCESS),
      "?q=ACME",
    );
  });

  it("sincroniza a URL somente enquanto a lista da Carteira é a rota ativa", () => {
    assert.equal(
      isCustomersListPathname("/apps/commercial/customers", "/apps/commercial"),
      true,
    );
    assert.equal(
      isCustomersListPathname("/apps/commercial/customers/", "/apps/commercial"),
      true,
    );
    for (const pathname of [
      "/apps/commercial",
      "/apps/commercial/open-orders",
      "/apps/commercial/customers/000001/01",
      "/apps/commercial/analytics",
    ]) {
      assert.equal(
        isCustomersListPathname(pathname, "/apps/commercial"),
        false,
        pathname,
      );
    }
  });
});

describe("updateCustomersListState", () => {
  const state = {
    q: "ACME", focus: "growth", sellerId: "seller-1",
    sort: "nome", dir: "asc", page: 7,
  };
  for (const change of [
    { q: "BETA" },
    { focus: "attention" },
    { sellerId: "seller-2" },
    { sort: "billed12m", dir: "desc" },
  ]) {
    it(`reseta pagina ao alterar ${Object.keys(change).join("/")}`, () => {
      assert.equal(updateCustomersListState(state, change).page, 1);
    });
  }
  it("preserva pagina quando somente a pagina muda", () => {
    assert.equal(updateCustomersListState(state, { page: 3 }).page, 3);
  });
});
