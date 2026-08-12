#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { describe, it } from "node:test";

import {
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildPluginPath,
  resolveActiveNavId,
  resolvePluginRoute,
} from "./pluginRoutes.ts";
import { buildOpenOrdersContextSearch } from "../utils/openOrdersDeepLink.ts";

describe("rotas nativas do pedido comercial", () => {
  it("faz roundtrip da linha com segmentos codificados", () => {
    const path = buildOpenOrderLineDetailPath(
      "/apps/commercial",
      "01",
      "PED/42",
      "01 A",
      "?stock=parcial&seller_id=vendedor-1",
    );
    assert.equal(
      path,
      "/apps/commercial/open-orders/01/PED%2F42/01%20A?stock=parcial&seller_id=vendedor-1",
    );
    assert.deepEqual(resolvePluginRoute(path, "/apps/commercial"), {
      view: "open_order_line_detail",
      pathname: "/apps/commercial/open-orders/01/PED%2F42/01%20A",
      relativePath: "open-orders/01/PED%2F42/01%20A",
      orderBranch: "01",
      orderNumber: "PED/42",
      lineItem: "01 A",
    });
  });

  it("faz roundtrip de segmentos codificados", () => {
    const path = buildOpenOrderOpDetailPath(
      "/apps/commercial",
      "01",
      "PED/42",
      "01 A",
      "OP#9",
      "?seller_id=vendedor-1",
    );
    assert.equal(
      path,
      "/apps/commercial/open-orders/01/PED%2F42/01%20A/op/OP%239?seller_id=vendedor-1",
    );
    assert.deepEqual(resolvePluginRoute(path, "/apps/commercial"), {
      view: "open_order_op_detail",
      pathname: "/apps/commercial/open-orders/01/PED%2F42/01%20A/op/OP%239",
      relativePath: "open-orders/01/PED%2F42/01%20A/op/OP%239",
      orderBranch: "01",
      orderNumber: "PED/42",
      lineItem: "01 A",
      productionOrder: "OP#9",
    });
  });

  it("rejeita builder incompleto e segmento inválido", () => {
    assert.equal(
      buildOpenOrderOpDetailPath("/apps/commercial", "01", "P1", "", "OP1"),
      null,
    );
    assert.equal(
      resolvePluginRoute(
        "/apps/commercial/open-orders/01/P1/01/op/%E0%A4%A",
        "/apps/commercial",
      ).view,
      "not_found",
    );
  });

  it("mantém Pedidos como navegação ativa", () => {
    assert.equal(resolveActiveNavId("open_order_line_detail"), "open_orders");
    assert.equal(resolveActiveNavId("open_order_op_detail"), "open_orders");
  });

  it("preserva contexto no fluxo lista → linha → OP → linha/lista", () => {
    const context = buildOpenOrdersContextSearch(
      "?q=motor&branch=01&client=000001&stock=parcial&focus=late&seller_id=s1&sort=produto&dir=desc&page=4&pedido=ignorar&linha=ignorar&externo=1",
      { allowSellerId: true, validSellerIds: ["s1"] },
    );
    const listPath = buildPluginPath("open_orders", "/apps/commercial", context);
    const linePath = buildOpenOrderLineDetailPath(
      "/apps/commercial",
      "01",
      "000123",
      "02",
      context,
    );
    const opPath = buildOpenOrderOpDetailPath(
      "/apps/commercial",
      "01",
      "000123",
      "02",
      "OP-9",
      context,
    );

    assert.equal(
      context,
      "?q=motor&branch=01&client=000001&stock=parcial&focus=late&seller_id=s1&sort=produto&dir=desc&page=4",
    );
    assert.equal(
      listPath,
      `/apps/commercial/open-orders${context}`,
    );
    assert.equal(
      linePath,
      `/apps/commercial/open-orders/01/000123/02${context}`,
    );
    assert.equal(
      opPath,
      `/apps/commercial/open-orders/01/000123/02/op/OP-9${context}`,
    );
    assert.equal(resolvePluginRoute(linePath, "/apps/commercial").view, "open_order_line_detail");
    assert.equal(resolvePluginRoute(opPath, "/apps/commercial").view, "open_order_op_detail");
  });
});

describe("estrutura dos detalhes de linha e OP", () => {
  it("as duas páginas compartilham o conteúdo operacional integral", async () => {
    const [linePage, opPage, content, app, table, otdPanel, otdUtils] = await Promise.all([
      readFile(
        new URL("../features/open-orders/OpenOrderLineDetailPage.tsx", import.meta.url),
        "utf8",
      ),
      readFile(
        new URL("../features/open-orders/OpenOrderOpDetailPage.tsx", import.meta.url),
        "utf8",
      ),
      readFile(
        new URL("../components/OpenOrdersProductionDetailContent.tsx", import.meta.url),
        "utf8",
      ),
      readFile(new URL("../App.tsx", import.meta.url), "utf8"),
      readFile(new URL("../components/OpenOrdersTable.tsx", import.meta.url), "utf8"),
      readFile(new URL("../components/OpenOrdersOtdPiPanel.tsx", import.meta.url), "utf8"),
      readFile(new URL("../utils/productionOtdLink.ts", import.meta.url), "utf8"),
    ]);
    assert.match(linePage, /<OpenOrdersProductionDetailContent/);
    assert.match(opPage, /<OpenOrdersProductionDetailContent/);
    assert.match(linePage, /usePortfolioSellerAccess/);
    assert.match(linePage, /resolveOpenOrdersSellerId/);
    assert.match(opPage, /usePortfolioSellerAccess/);
    assert.match(opPage, /resolveOpenOrdersSellerId/);
    assert.match(opPage, /showOpenProductionOrderAction=\{false\}/);
    assert.match(opPage, /Produto \$\{item\.produto\.trim\(\)\}/);
    assert.match(content, /export function OpenOrdersProductionDetailContent/);
    assert.match(content, /CommercialDataRecordCard/);
    const removedTableSymbols = new RegExp(
      [
        ["Commercial", "Workbench", "Modal"].join(""),
        "detailItem",
        "syncOpenOrdersLineQuery",
      ].join("|"),
    );
    assert.doesNotMatch(table, removedTableSymbols);
    assert.match(table, /navigateOpenOrderLineDetail/);
    assert.match(table, /parseOpenOrdersLineDeepLink/);
    assert.match(table, /findOpenOrderLine/);
    assert.match(table, /replace:\s*true/);
    assert.match(app, /view === "open_order_line_detail"/);
    assert.match(app, /view === "open_order_op_detail"/);
    assert.match(app, /<OpenOrderLineDetailPage/);
    assert.match(app, /<OpenOrderOpDetailPage/);
    for (const source of [linePage, opPage, otdPanel, otdUtils]) {
      assert.doesNotMatch(source, /dashboard-production|production-appointments|iframe/i);
    }
  });

  it("mantém cards mobile e PagePath determinístico nos detalhes", async () => {
    const [opportunity, otdLine] = await Promise.all([
      readFile(
        new URL("../features/analytics/AnalyticsOpportunityDetailPage.tsx", import.meta.url),
        "utf8",
      ),
      readFile(
        new URL("../features/analytics/AnalyticsOtdLineDetailPage.tsx", import.meta.url),
        "utf8",
      ),
    ]);
    assert.match(opportunity, /CommercialDataRecordCard/);
    assert.match(opportunity, /cm-responsive-records__mobile/);
    assert.match(otdLine, /<CommercialPagePath/);
    assert.match(otdLine, /buildPluginPath\(/);
    assert.doesNotMatch(otdLine, /ArrowLeft/);
  });

  it("mantém OV exclusivamente como página navegada pelo helper", async () => {
    const files = await Promise.all(
      [
        "../features/analytics/AnalyticsOpportunitiesPage.tsx",
        "../features/analytics/AnalyticsPage.tsx",
        "../components/OpenOrdersProductionDetailContent.tsx",
      ].map((path) => readFile(new URL(path, import.meta.url), "utf8")),
    );
    for (const source of files) {
      assert.match(source, /navigateAnalyticsOpportunityDetail/);
      assert.doesNotMatch(source, /OpportunityDetailModal|OvDetailModal/);
    }
  });
});
