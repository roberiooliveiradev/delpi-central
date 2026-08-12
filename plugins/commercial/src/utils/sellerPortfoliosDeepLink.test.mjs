#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildSellerPortfolioDetailPath,
  buildSellerPortfoliosPath,
  buildSellerPortfoliosSearch,
  isSellerPortfoliosPathname,
  migrateLegacySellerPortfolioIdParam,
  parseSellerPortfolioDetailRouteState,
  parseSellerPortfoliosDeepLink,
  parseSellerPortfoliosRouteState,
  replaceSellerPortfoliosSearch,
  sanitizeSellerPortfoliosSearch,
} from "./sellerPortfoliosDeepLink.ts";

const PORTFOLIO_ID = "11111111-1111-4111-8111-111111111111";

describe("sellerPortfoliosDeepLink", () => {
  it("parseia somente o estado reconhecido da lista (sem id)", () => {
    assert.deepEqual(
      parseSellerPortfoliosDeepLink(
        `?q=%20Ana%20&filter=inactive&view=org&axis=person&id=${PORTFOLIO_ID}&external=https://example.com`,
      ),
      {
        q: "Ana",
        filter: "inactive",
        view: "org",
        axis: "person",
      },
    );
  });

  it("normaliza filtro/view/axis inválidos e omite defaults", () => {
    assert.deepEqual(parseSellerPortfoliosDeepLink("?q=%20%20&filter=late&view=tree&axis=x&id=not-a-uuid"), {
      q: "",
      filter: "all",
      view: "list",
      axis: "portfolio",
    });
    assert.deepEqual(parseSellerPortfoliosDeepLink("?filter=overlapping"), {
      q: "",
      filter: "overlapping",
      view: "list",
      axis: "portfolio",
    });
    assert.equal(
      sanitizeSellerPortfoliosSearch(`?filter=all&view=list&axis=portfolio&id=${PORTFOLIO_ID}&redirect=/apps/other`),
      "",
    );
    assert.equal(buildSellerPortfoliosSearch({ q: "", filter: "all", view: "list", axis: "portfolio" }), "");
    assert.equal(
      buildSellerPortfoliosSearch({ q: "", filter: "active", view: "org", axis: "person" }),
      "?filter=active&view=org&axis=person",
    );
    assert.equal(
      buildSellerPortfoliosSearch({ q: "", filter: "overlapping", view: "list", axis: "portfolio" }),
      "?filter=overlapping",
    );
  });

  it("só reconhece a rota exata de carteiras (lista)", () => {
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
      buildSellerPortfoliosPath("/apps/commercial", { filter: "active", q: "bruno", view: "org" }),
      "/apps/commercial/seller-portfolios?q=bruno&filter=active&view=org",
    );
  });

  it("monta e parseia detalhe /seller-portfolios/:id preservando query da lista", () => {
    assert.equal(
      buildSellerPortfolioDetailPath("/apps/commercial", PORTFOLIO_ID, {
        filter: "active",
        q: "ana",
        view: "org",
        axis: "person",
      }),
      `/apps/commercial/seller-portfolios/${PORTFOLIO_ID}?q=ana&filter=active&view=org&axis=person`,
    );
    assert.deepEqual(
      parseSellerPortfolioDetailRouteState(
        `/apps/commercial/seller-portfolios/${PORTFOLIO_ID}`,
        "?filter=inactive&view=org",
        "/apps/commercial",
      ),
      {
        portfolioId: PORTFOLIO_ID,
        list: { q: "", filter: "inactive", view: "org", axis: "portfolio" },
      },
    );
    assert.equal(
      parseSellerPortfolioDetailRouteState(
        "/apps/commercial/seller-portfolios",
        `?id=${PORTFOLIO_ID}`,
        "/apps/commercial",
      ),
      null,
    );
  });

  it("migra legado ?id= na lista para o path de detalhe", () => {
    assert.equal(
      migrateLegacySellerPortfolioIdParam(
        "/apps/commercial/seller-portfolios",
        `?id=${PORTFOLIO_ID}&filter=active&view=org`,
        "/apps/commercial",
      ),
      `/apps/commercial/seller-portfolios/${PORTFOLIO_ID}?filter=active&view=org`,
    );
    assert.equal(
      migrateLegacySellerPortfolioIdParam(
        "/apps/commercial/seller-portfolios",
        "?filter=active",
        "/apps/commercial",
      ),
      null,
    );
    assert.equal(
      migrateLegacySellerPortfolioIdParam(
        `/apps/commercial/seller-portfolios/${PORTFOLIO_ID}`,
        `?id=${PORTFOLIO_ID}`,
        "/apps/commercial",
      ),
      null,
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
    replaceSellerPortfoliosSearch("/apps/commercial", { filter: "active", view: "org" });
    assert.equal(replacements.length, 1);
    assert.equal(
      replacements[0][2],
      "/apps/commercial/seller-portfolios?filter=active&view=org",
    );

    globalThis.window.history = original.history;
    globalThis.window.location = original.location;
  });
});
