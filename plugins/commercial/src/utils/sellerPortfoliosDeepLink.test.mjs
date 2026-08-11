#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildSellerPortfoliosPath,
  buildSellerPortfoliosSearch,
  isSellerPortfoliosPathname,
  parseSellerPortfoliosDeepLink,
  parseSellerPortfoliosRouteState,
  replaceSellerPortfoliosSearch,
  sanitizeSellerPortfoliosSearch,
} from "./sellerPortfoliosDeepLink.ts";

const PORTFOLIO_ID = "11111111-1111-4111-8111-111111111111";

describe("sellerPortfoliosDeepLink", () => {
  it("parseia somente o estado reconhecido", () => {
    assert.deepEqual(
      parseSellerPortfoliosDeepLink(
        `?q=%20Ana%20&filter=inactive&id=${PORTFOLIO_ID}&external=https://example.com`,
      ),
      {
        q: "Ana",
        filter: "inactive",
        id: PORTFOLIO_ID,
      },
    );
  });

  it("normaliza filtro e id inválidos e omite defaults", () => {
    assert.deepEqual(parseSellerPortfoliosDeepLink("?q=%20%20&filter=late&id=not-a-uuid"), {
      q: "",
      filter: "all",
      id: null,
    });
    assert.equal(
      sanitizeSellerPortfoliosSearch(`?filter=all&id=${PORTFOLIO_ID}&redirect=/apps/other`),
      `?id=${PORTFOLIO_ID}`,
    );
    assert.equal(buildSellerPortfoliosSearch({ q: "", filter: "all", id: null }), "");
  });

  it("só reconhece a rota exata de carteiras", () => {
    assert.equal(
      isSellerPortfoliosPathname("/apps/commercial/seller-portfolios", "/apps/commercial"),
      true,
    );
    assert.equal(
      isSellerPortfoliosPathname("/apps/commercial/seller-portfolios/extra", "/apps/commercial"),
      false,
    );
    assert.equal(
      parseSellerPortfoliosRouteState(
        "/apps/commercial/customers",
        `?id=${PORTFOLIO_ID}`,
        "/apps/commercial",
      ),
      null,
    );
    assert.equal(
      buildSellerPortfoliosPath("/apps/commercial", { filter: "active", q: "bruno" }),
      "/apps/commercial/seller-portfolios?q=bruno&filter=active",
    );
  });

  it("faz replaceState somente na lista /seller-portfolios", () => {
    const replacements = [];
    const original = {
      pathname: "/apps/commercial/customers",
      search: "",
      history: globalThis.window?.history,
      location: globalThis.window?.location,
    };
    globalThis.window = {
      location: { pathname: "/apps/commercial/customers", search: "" },
      history: {
        state: null,
        replaceState: (...args) => replacements.push(args),
      },
    };
    replaceSellerPortfoliosSearch("/apps/commercial", { filter: "active" });
    assert.equal(replacements.length, 0);

    globalThis.window.location = {
      pathname: "/apps/commercial/seller-portfolios",
      search: "",
    };
    replaceSellerPortfoliosSearch("/apps/commercial", { filter: "active" });
    assert.equal(replacements.length, 1);
    assert.equal(
      replacements[0][2],
      "/apps/commercial/seller-portfolios?filter=active",
    );

    globalThis.window.history = original.history;
    globalThis.window.location = original.location;
  });
});
