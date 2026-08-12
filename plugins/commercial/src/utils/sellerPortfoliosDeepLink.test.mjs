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
const ADMIN_LIST = "/apps/commercial/administration/seller-portfolios";
const LEGACY_LIST = "/apps/commercial/seller-portfolios";

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
    assert.deepEqual(parseSellerPortfoliosDeepLink("?filter=uncovered"), {
      q: "",
      filter: "uncovered",
      view: "list",
      axis: "portfolio",
    });
    assert.equal(
      buildSellerPortfoliosSearch({ q: "", filter: "uncovered", view: "list", axis: "portfolio" }),
      "?filter=uncovered",
    );
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

  it("reconhece lista canônica admin e alias legado", () => {
    assert.equal(isSellerPortfoliosPathname(ADMIN_LIST, "/apps/commercial"), true);
    assert.equal(isSellerPortfoliosPathname(LEGACY_LIST, "/apps/commercial"), true);
    assert.equal(
      isSellerPortfoliosPathname(`${ADMIN_LIST}/extra`, "/apps/commercial"),
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
      `${ADMIN_LIST}?q=bruno&filter=active&view=org`,
    );
  });

  it("monta e parseia detalhe admin/:id preservando query da lista", () => {
    assert.equal(
      buildSellerPortfolioDetailPath("/apps/commercial", PORTFOLIO_ID, {
        filter: "active",
        q: "ana",
        view: "org",
        axis: "person",
      }),
      `${ADMIN_LIST}/${PORTFOLIO_ID}?q=ana&filter=active&view=org&axis=person`,
    );
    assert.deepEqual(
      parseSellerPortfolioDetailRouteState(
        `${ADMIN_LIST}/${PORTFOLIO_ID}`,
        "?filter=inactive&view=org",
        "/apps/commercial",
      ),
      {
        portfolioId: PORTFOLIO_ID,
        list: { q: "", filter: "inactive", view: "org", axis: "portfolio" },
      },
    );
    assert.deepEqual(
      parseSellerPortfolioDetailRouteState(
        `${LEGACY_LIST}/${PORTFOLIO_ID}`,
        "?filter=active",
        "/apps/commercial",
      ),
      {
        portfolioId: PORTFOLIO_ID,
        list: { q: "", filter: "active", view: "list", axis: "portfolio" },
      },
    );
    assert.equal(
      parseSellerPortfolioDetailRouteState(ADMIN_LIST, `?id=${PORTFOLIO_ID}`, "/apps/commercial"),
      null,
    );
  });

  it("migra legado ?id= na lista para o path de detalhe admin", () => {
    assert.equal(
      migrateLegacySellerPortfolioIdParam(
        LEGACY_LIST,
        `?id=${PORTFOLIO_ID}&filter=active&view=org`,
        "/apps/commercial",
      ),
      `${ADMIN_LIST}/${PORTFOLIO_ID}?filter=active&view=org`,
    );
    assert.equal(
      migrateLegacySellerPortfolioIdParam(ADMIN_LIST, "?filter=active", "/apps/commercial"),
      null,
    );
    assert.equal(
      migrateLegacySellerPortfolioIdParam(
        `${ADMIN_LIST}/${PORTFOLIO_ID}`,
        `?id=${PORTFOLIO_ID}`,
        "/apps/commercial",
      ),
      null,
    );
  });

  it("faz replaceState na lista admin ou legado (canonicaliza para admin)", () => {
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
      pathname: LEGACY_LIST,
      search: "",
    };
    replaceSellerPortfoliosSearch("/apps/commercial", { filter: "active", view: "org" });
    assert.equal(replacements.length, 1);
    assert.equal(replacements[0][2], `${ADMIN_LIST}?filter=active&view=org`);

    globalThis.window.history = original.history;
    globalThis.window.location = original.location;
  });
});
