#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCustomersListPath,
  buildCustomersListSearch,
  parseCustomersListDeepLink,
  sanitizeCustomersListSearch,
} from "./customersListDeepLink.ts";

const TEAM_ACCESS = {
  allowSellerId: true,
  validSellerIds: ["seller-1", "seller-2"],
};

describe("customersListDeepLink", () => {
  it("parseia somente o estado reconhecido", () => {
    assert.deepEqual(
      parseCustomersListDeepLink(
        "?q=%20Acme%20&focus=growth&seller_id=seller-2&external=https://example.com",
        TEAM_ACCESS,
      ),
      {
        q: "Acme",
        focus: "growth",
        sellerId: "seller-2",
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
      },
    );
  });

  it("mantém roundtrip canônico e rota interna", () => {
    const state = {
      q: "Metalúrgica A",
      focus: "attention",
      sellerId: "seller-1",
    };
    const search = buildCustomersListSearch(state, TEAM_ACCESS);
    assert.equal(search, "?q=Metal%C3%BArgica+A&focus=attention&seller_id=seller-1");
    assert.deepEqual(parseCustomersListDeepLink(search, TEAM_ACCESS), state);
    assert.equal(
      buildCustomersListPath("https://malicioso.example", state, TEAM_ACCESS),
      "/apps/commercial/customers?q=Metal%C3%BArgica+A&focus=attention&seller_id=seller-1",
    );
  });
});
