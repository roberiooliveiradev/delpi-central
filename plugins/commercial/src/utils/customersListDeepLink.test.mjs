#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCustomersListPath,
  buildCustomersListSearch,
  isCustomersListPathname,
  parseCustomersListDeepLink,
  parseCustomersListRouteState,
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
        "?q=%20Acme%20&focus=active&trend=down&seller_id=seller-2&sort=billed12m&dir=desc&page=3&external=https://example.com",
        TEAM_ACCESS,
      ),
      {
        q: "Acme",
        focus: "active",
        trend: "down",
        sellerId: "seller-2",
        sort: "billed12m",
        dir: "desc",
        page: 3,
        panel: "customers",
        billingNature: "gross",
      },
    );
  });

  it("normaliza foco e vendedor inválidos", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?q=%20%20&focus=late&seller_id=unknown", TEAM_ACCESS),
      {
        q: "",
        focus: "all",
        trend: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
        panel: "customers",
        billingNature: "gross",
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
        trend: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
        panel: "customers",
        billingNature: "gross",
      },
    );
  });

  it("persiste billingNature=net na URL e default gross omite o param", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?billingNature=net&panel=billing", TEAM_ACCESS),
      {
        q: "",
        focus: "all",
        trend: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
        panel: "billing",
        billingNature: "net",
      },
    );
    assert.equal(
      buildCustomersListSearch(
        { panel: "billing", billingNature: "net" },
        TEAM_ACCESS,
      ),
      "?panel=billing&billingNature=net",
    );
    assert.equal(
      buildCustomersListSearch({ billingNature: "gross" }, TEAM_ACCESS),
      "",
    );
  });

  it("mapeia focus=growth legado para tendência de alta", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?focus=growth", TEAM_ACCESS),
      {
        q: "",
        focus: "all",
        trend: "up",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
        panel: "customers",
        billingNature: "gross",
      },
    );
    assert.equal(sanitizeCustomersListSearch("?focus=growth", TEAM_ACCESS), "?trend=up");
    assert.equal(sanitizeCustomersListSearch("?focus=inactive", TEAM_ACCESS), "");
    assert.equal(
      sanitizeCustomersListSearch("?focus=growth&trend=down", TEAM_ACCESS),
      "?trend=down",
    );
  });

  it("mantém roundtrip canônico e rota interna", () => {
    const state = {
      q: "Metalúrgica A",
      focus: "attention",
      trend: "down",
      sellerId: "seller-1",
      sort: "lastPurchaseDate",
      dir: "desc",
      page: 4,
      panel: "customers",
      billingNature: "gross",
    };
    const search = buildCustomersListSearch(state, TEAM_ACCESS);
    assert.equal(search, "?q=Metal%C3%BArgica+A&focus=attention&trend=down&seller_id=seller-1&sort=lastPurchaseDate&dir=desc&page=4");
    assert.deepEqual(parseCustomersListDeepLink(search, TEAM_ACCESS), state);
    assert.equal(
      buildCustomersListPath("https://malicioso.example", state, TEAM_ACCESS),
      "/apps/commercial/customers?q=Metal%C3%BArgica+A&focus=attention&trend=down&seller_id=seller-1&sort=lastPurchaseDate&dir=desc&page=4",
    );
  });

  it("aplica defaults e remove toda query fora da allowlist", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?focus=x&sort=__proto__&dir=up&page=-2&unknown=1", TEAM_ACCESS),
      { q: "", focus: "all", trend: "all", sellerId: null, sort: "attention", dir: "asc", page: 1, panel: "customers", billingNature: "gross" },
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

  it("ignora popstate de outra página sem alterar o escopo da Carteira", () => {
    assert.equal(
      parseCustomersListRouteState(
        "/apps/commercial/open-orders",
        "?seller_id=seller-2&q=nao-aplicar",
        "/apps/commercial",
        TEAM_ACCESS,
      ),
      null,
    );
    assert.deepEqual(
      parseCustomersListRouteState(
        "/apps/commercial/customers",
        "?seller_id=seller-2&q=Acme&page=2",
        "/apps/commercial",
        TEAM_ACCESS,
      ),
      {
        q: "Acme",
        focus: "all",
        trend: "all",
        sellerId: "seller-2",
        sort: "attention",
        dir: "asc",
        page: 2,
        panel: "customers",
      billingNature: "gross",
      },
    );
  });

  it("persiste panel na query e defaulta customers", () => {
    assert.deepEqual(
      parseCustomersListDeepLink("?panel=billing", TEAM_ACCESS),
      {
        q: "",
        focus: "all",
        trend: "all",
        sellerId: null,
        sort: "attention",
        dir: "asc",
        page: 1,
        panel: "billing",
      billingNature: "gross",
      },
    );
    assert.equal(
      buildCustomersListSearch(
        {
          q: "",
          focus: "all",
          trend: "all",
          sellerId: null,
          sort: "attention",
          dir: "asc",
          page: 1,
          panel: "ranking",
        billingNature: "gross",
        },
        TEAM_ACCESS,
      ),
      "?panel=ranking",
    );
    assert.equal(
      sanitizeCustomersListSearch("?panel=customers&unknown=1", TEAM_ACCESS),
      "",
    );
    assert.equal(
      parseCustomersListDeepLink("?panel=nope", TEAM_ACCESS).panel,
      "customers",
    );
  });
});

describe("updateCustomersListState", () => {
  const state = {
    q: "ACME", focus: "active", trend: "up", sellerId: "seller-1",
    sort: "nome", dir: "asc", page: 7, panel: "customers",
    billingNature: "gross",
  };
  for (const change of [
    { q: "BETA" },
    { focus: "attention" },
    { trend: "down" },
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
  it("preserva pagina ao trocar panel", () => {
    assert.equal(updateCustomersListState(state, { panel: "billing" }).page, 7);
    assert.equal(updateCustomersListState(state, { panel: "billing" }).panel, "billing");
  });
});
