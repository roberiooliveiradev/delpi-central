#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  buildCommercialOpenOrderPath,
  buildOpenOrdersListSearch,
  buildOpenOrdersContextSearch,
  findOpenOrderLine,
  isOpenOrdersListPath,
  parseOpenOrdersAttentionDeepLink,
  parseOpenOrdersLineDeepLink,
  parseOpenOrdersListRouteState,
  parseOpenOrdersListUrlState,
  resolveOpenOrdersSellerId,
  sanitizeOpenOrdersListSearch,
  syncOpenOrdersListStateToUrl,
} from "./openOrdersDeepLink.ts";

describe("openOrdersDeepLink", () => {
  it("monta path com pedido linha e filial", () => {
    assert.equal(
      buildCommercialOpenOrderPath({
        pedido: "123",
        linha: "01",
        filial: "02",
      }),
      "/apps/commercial/open-orders?pedido=123&linha=01&filial=02",
    );
  });

  it("monta path só com pedido", () => {
    assert.equal(
      buildCommercialOpenOrderPath({ pedido: "123", filial: "01" }),
      "/apps/commercial/open-orders?pedido=123&filial=01",
    );
  });

  it("parseia atenção e linha", () => {
    assert.deepEqual(
      parseOpenOrdersAttentionDeepLink("?stock=parcial&focus=late"),
      { stockStatus: "parcial", lateOnly: true },
    );
    assert.deepEqual(parseOpenOrdersLineDeepLink("?pedido=9&linha=02&filial=01"), {
      pedido: "9",
      linha: "02",
      filial: "01",
    });
    assert.deepEqual(parseOpenOrdersLineDeepLink("?pedido=9"), {
      pedido: "9",
      linha: undefined,
      filial: undefined,
    });
    assert.equal(parseOpenOrdersLineDeepLink("?linha=01"), null);
  });

  it("preserva todo o estado canônico ao abrir linha e OP", () => {
    assert.equal(
      buildOpenOrdersContextSearch(
        "?q=motor&branch=01&client=ACME&client=DELPI&stock=parcial&focus=late&date_start=2026-08-01&date_end=2026-08-31&seller_id=v1&sort=produto&dir=desc&page=3&pedido=9&extra=x",
      ),
      "?q=motor&branch=01&client=ACME&client=DELPI&stock=parcial&focus=late&date_start=2026-08-01&date_end=2026-08-31&seller_id=v1&sort=produto&dir=desc&page=3",
    );
    assert.equal(
      buildOpenOrdersContextSearch("?stock=invalido&focus=atraso&seller_id=v2"),
      "?seller_id=v2",
    );
  });

  it("aplica allowlist, defaults e RBAC de seller_id", () => {
    const state = parseOpenOrdersListUrlState(
      "?q=x&branch=02&client=A&client=A&client=B&stock=invalido&focus=atraso&date_start=2026-02-30&date_end=2026-08-10&seller_id=s2&sort=hack&dir=side&page=-5&extra=1",
      { allowSellerId: true, validSellerIds: ["s1", "s2"] },
    );
    assert.deepEqual(state.filters, {
      search: "x",
      filial: "02",
      clientCodes: ["A", "B"],
      stockStatus: "",
      dateStart: "",
      dateEnd: "2026-08-10",
      lateOnly: false,
    });
    assert.equal(state.sellerId, "s2");
    assert.equal(state.sortKey, "data_entrega");
    assert.equal(state.sortDirection, "asc");
    assert.equal(state.page, 1);
    assert.equal(
      sanitizeOpenOrdersListSearch("?seller_id=s2&sort=hack&page=0", {
        allowSellerId: false,
        validSellerIds: ["s2"],
      }),
      "",
    );
    assert.equal(resolveOpenOrdersSellerId("s2", {
      allowSellerId: true,
      validSellerIds: ["s1"],
    }), null);
  });

  it("omite defaults e serializa filtros, sort e página deterministicamente", () => {
    const state = parseOpenOrdersListUrlState(
      "?q=abc&branch=01&client=C1&stock=com_estoque&date_start=2026-08-01&seller_id=s1&sort=pedido&dir=desc&page=2",
      { allowSellerId: true, validSellerIds: ["s1"] },
    );
    assert.equal(
      buildOpenOrdersListSearch(state),
      "?q=abc&branch=01&client=C1&stock=com_estoque&date_start=2026-08-01&seller_id=s1&sort=pedido&dir=desc&page=2",
    );
  });

  it("faz replaceState somente na lista /open-orders", () => {
    const originalWindow = globalThis.window;
    const replacements = [];
    const state = parseOpenOrdersListUrlState("?q=novo");
    globalThis.window = {
      location: {
        href: "https://example.test/apps/commercial/open-orders?q=antigo",
        pathname: "/apps/commercial/open-orders",
        search: "?q=antigo",
      },
      history: {
        state: { preserved: true },
        replaceState: (...args) => replacements.push(args),
      },
    };
    try {
      syncOpenOrdersListStateToUrl(state);
      assert.equal(replacements.length, 1);
      assert.equal(replacements[0][2], "/apps/commercial/open-orders?q=novo");
      globalThis.window.location.pathname = "/apps/commercial/open-orders/01/123/01";
      syncOpenOrdersListStateToUrl(state);
      assert.equal(replacements.length, 1);
      assert.equal(isOpenOrdersListPath("/apps/commercial/open-orders/"), true);
      assert.equal(isOpenOrdersListPath("/apps/commercial/open-orders/01"), false);
    } finally {
      globalThis.window = originalWindow;
    }
  });

  it("ignora popstate de detalhe ou de outra página", () => {
    const access = { allowSellerId: true, validSellerIds: ["s1"] };
    for (const pathname of [
      "/apps/commercial/open-orders/01/123/01",
      "/apps/commercial/open-orders/01/123/01/op/OP1",
      "/apps/commercial/customers",
    ]) {
      assert.equal(
        parseOpenOrdersListRouteState(
          pathname,
          "?seller_id=s1&q=nao-aplicar",
          "/apps/commercial",
          access,
        ),
        null,
      );
    }
    assert.equal(
      parseOpenOrdersListRouteState(
        "/apps/commercial/open-orders",
        "?seller_id=s1&page=3",
        "/apps/commercial",
        access,
      )?.sellerId,
      "s1",
    );
  });

  it("encontra linha na lista", () => {
    const hit = findOpenOrderLine(
      [
        { filial: "01", pedido: "A", linha: "01" },
        { filial: "02", pedido: "B", linha: "02" },
      ],
      { pedido: "B", linha: "02", filial: "02" },
    );
    assert.equal(hit?.pedido, "B");
  });

  it("encontra primeira linha quando só pedido", () => {
    const hit = findOpenOrderLine(
      [
        { filial: "01", pedido: "A", linha: "01" },
        { filial: "01", pedido: "A", linha: "02" },
      ],
      { pedido: "A" },
    );
    assert.equal(hit?.linha, "01");
  });
});
