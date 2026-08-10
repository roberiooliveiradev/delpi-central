#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { describe, it } from "node:test";

import {
  buildOpenOrderOpDetailPath,
  resolveActiveNavId,
  resolvePluginRoute,
} from "./pluginRoutes.ts";

describe("rota nativa da OP comercial", () => {
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
    assert.equal(resolveActiveNavId("open_order_op_detail"), "open_orders");
  });
});

describe("estrutura do detalhe OP", () => {
  it("página e modal compartilham o conteúdo operacional sem URL de outro plugin", async () => {
    const [page, modal, app, otdPanel, otdUtils] = await Promise.all([
      readFile(
        new URL("../features/open-orders/OpenOrderOpDetailPage.tsx", import.meta.url),
        "utf8",
      ),
      readFile(new URL("../components/OpenOrdersLineDetailModal.tsx", import.meta.url), "utf8"),
      readFile(new URL("../App.tsx", import.meta.url), "utf8"),
      readFile(new URL("../components/OpenOrdersOtdPiPanel.tsx", import.meta.url), "utf8"),
      readFile(new URL("../utils/productionOtdLink.ts", import.meta.url), "utf8"),
    ]);
    assert.match(page, /OpenOrdersProductionDetailContent/);
    assert.match(modal, /export function OpenOrdersProductionDetailContent/);
    assert.match(modal, /<OpenOrdersProductionDetailContent/);
    assert.match(app, /view === "open_order_op_detail"/);
    assert.match(app, /<OpenOrderOpDetailPage/);
    for (const source of [page, otdPanel, otdUtils]) {
      assert.doesNotMatch(source, /dashboard-production|production-appointments|iframe/i);
    }
  });

  it("mantém OV exclusivamente como página navegada pelo helper", async () => {
    const files = await Promise.all(
      [
        "../features/analytics/AnalyticsOpportunitiesPage.tsx",
        "../features/analytics/AnalyticsPage.tsx",
        "../components/OpenOrdersLineDetailModal.tsx",
      ].map((path) => readFile(new URL(path, import.meta.url), "utf8")),
    );
    for (const source of files) {
      assert.match(source, /navigateAnalyticsOpportunityDetail/);
      assert.doesNotMatch(source, /OpportunityDetailModal|OvDetailModal/);
    }
  });
});
