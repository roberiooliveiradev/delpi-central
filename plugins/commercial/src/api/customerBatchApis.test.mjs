#!/usr/bin/env node
import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import { fetchCustomerBillingSeries } from "./customerBillingSeriesApi.ts";
import { enrichPortfolioCustomersBatched } from "./customerEnrichmentApi.ts";

const originalFetch = globalThis.fetch;
const customers = (count) => Array.from({ length: count }, (_, index) => ({
  customer_code: String(index + 1).padStart(6, "0"),
  customer_store: "01",
}));
const jsonResponse = (data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { "Content-Type": "application/json" },
});
afterEach(() => { globalThis.fetch = originalFetch; });

describe("APIs em lotes de clientes", () => {
  it("enrichment cobre 201+ clientes sem enviar mais de 200", async () => {
    const sizes = [];
    globalThis.fetch = async (_url, init) => {
      const body = JSON.parse(String(init?.body));
      sizes.push(body.customers.length);
      return jsonResponse({ success: true, data: { items: body.customers.map((customer) => ({
        ...customer, city: null, state: null, last_purchase_date: null,
        billed_12m: null, has_avatar: false, avatar_url: null,
      })) } });
    };
    const result = await enrichPortfolioCustomersBatched(customers(401));
    assert.equal(Math.max(...sizes), 200);
    assert.deepEqual(sizes.sort((a, b) => b - a), [200, 200, 1]);
    assert.deepEqual(result.coverage, { covered: 401, total: 401, failedBatches: 0 });
    assert.equal(result.partialError, null);
    assert.equal(result.items[0].billed_12m, null);
  });
  it("enrichment relata lote parcial e mantém merge estável", async () => {
    globalThis.fetch = async (_url, init) => {
      const body = JSON.parse(String(init?.body));
      if (body.customers[0].customer_code === "000201") {
        return jsonResponse({ message: "indisponível" }, 503);
      }
      return jsonResponse({ success: true, data: { items: [...body.customers].reverse().map((customer) => ({
        ...customer, city: customer.customer_code, state: null, last_purchase_date: null,
        billed_12m: null, has_avatar: false, avatar_url: null,
      })) } });
    };
    const result = await enrichPortfolioCustomersBatched(customers(201));
    assert.deepEqual(result.coverage, { covered: 200, total: 201, failedBatches: 1 });
    assert.match(result.partialError ?? "", /200 de 201/);
    assert.equal(result.items[0].customer_code, "000001");
    assert.equal(result.items.at(-1).customer_code, "000200");
  });
  it("faturamento agrega lotes e expõe cobertura parcial", async () => {
    const sizes = [];
    globalThis.fetch = async (_url, init) => {
      const body = JSON.parse(String(init?.body));
      sizes.push(body.customers.length);
      if (body.customers[0].customer_code === "000201") {
        return jsonResponse({ message: "indisponível" }, 503);
      }
      return jsonResponse({ success: true, data: {
        months: 12, customer_count: body.customers.length,
        points: [{ month: "2026-01", label: "Jan/26", value: body.customers.length,
          date_start: "2026-01-01", date_end: "2026-01-31" }],
      } });
    };
    const result = await fetchCustomerBillingSeries(customers(201));
    assert.equal(Math.max(...sizes), 200);
    assert.equal(result.points[0].value, 200);
    assert.deepEqual(result.coverage, { covered: 200, total: 201, failedBatches: 1 });
    assert.match(result.partialError ?? "", /200 de 201/);
  });
});
