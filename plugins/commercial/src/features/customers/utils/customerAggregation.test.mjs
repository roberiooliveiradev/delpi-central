#!/usr/bin/env node
/**
 * Testes puros da agregação de clientes (node:test, sem vitest).
 * Uso: node --experimental-strip-types --test src/features/customers/utils/customerAggregation.test.mjs
 */
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import {
  aggregateCustomers,
  isPartialDeliveryLine,
  toFiniteNumber,
} from "./customerAggregation.ts";
import { filterCustomers, matchesCustomerSearch } from "./customerFilters.ts";
import {
  buildCustomerKey,
  buildOrderKey,
  isValidCustomerIdentity,
  normalizeCadastroPart,
  parseCustomerKey,
} from "./customerIdentity.ts";
import {
  compareAttention,
  sortCustomersByAttention,
} from "./customerSorting.ts";
import { buildSellerNameByCustomerKey } from "./sellerNameByCustomer.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));

function line(overrides = {}) {
  return {
    nome_cliente: "ACME",
    tipo_entidade: "CLIENTE",
    tipo_pedido: "N",
    pedido_cliente: "PO-1",
    filial: "01",
    pedido: "100",
    linha: "01",
    produto: "P1",
    codigo_cliente: "PART",
    codigo_cadastro: "000123",
    loja_cadastro: "01",
    quantidade: 10,
    entregue: 0,
    saldo: 10,
    data_despacho: null,
    data_entrega: "2099-06-01",
    no_estoque: 0,
    preco_venda: 1,
    valor_aberto: 100,
    ...overrides,
  };
}

describe("customerIdentity", () => {
  it("combina codigo e loja", () => {
    assert.equal(buildCustomerKey("000123", "01"), "000123|01");
  });

  it("preserva zeros a esquerda", () => {
    assert.equal(normalizeCadastroPart("000123"), "000123");
    assert.equal(buildCustomerKey("000123", "01"), "000123|01");
    assert.notEqual(buildCustomerKey("000123", "01"), buildCustomerKey("123", "01"));
  });

  it("separa lojas diferentes", () => {
    assert.notEqual(buildCustomerKey("000123", "01"), buildCustomerKey("000123", "02"));
  });

  it("nao usa nome", () => {
    const key = buildCustomerKey("1", "01");
    assert.equal(key, "1|01");
    assert.ok(key && !key.includes("ACME"));
  });

  it("rejeita codigo vazio", () => {
    assert.equal(buildCustomerKey("", "01"), null);
    assert.equal(buildCustomerKey("   ", "01"), null);
    assert.equal(isValidCustomerIdentity("", "01"), false);
  });

  it("rejeita loja vazia", () => {
    assert.equal(buildCustomerKey("000123", ""), null);
    assert.equal(buildCustomerKey("000123", "  "), null);
    assert.equal(parseCustomerKey("000123|"), null);
  });
});

describe("customerAggregation", () => {
  it("agrupa linhas do mesmo cliente", () => {
    const result = aggregateCustomers([
      line({ pedido: "100", linha: "01" }),
      line({ pedido: "100", linha: "02", valor_aberto: 50 }),
    ]);
    assert.equal(result.customers.length, 1);
    assert.equal(result.customers[0].quantidadeLinhasAbertas, 2);
    assert.equal(result.customers[0].quantidadePedidosAbertos, 1);
  });

  it("nao mistura clientes distintos", () => {
    const result = aggregateCustomers([
      line({ codigo_cadastro: "000123", loja_cadastro: "01" }),
      line({ codigo_cadastro: "000123", loja_cadastro: "02", nome_cliente: "OUTRO" }),
    ]);
    assert.equal(result.customers.length, 2);
  });

  it("conta pedidos distintos por filial e pedido", () => {
    const result = aggregateCustomers([
      line({ filial: "01", pedido: "100", linha: "01" }),
      line({ filial: "01", pedido: "100", linha: "02" }),
      line({ filial: "02", pedido: "100", linha: "01", valor_aberto: 10 }),
    ]);
    assert.equal(result.customers[0].quantidadePedidosAbertos, 2);
    assert.equal(result.totalPedidosAbertos, 2);
    assert.equal(buildOrderKey("01", "100"), "01|100");
  });

  it("conta linhas separadamente", () => {
    const result = aggregateCustomers([
      line({ pedido: "100", linha: "01" }),
      line({ pedido: "200", linha: "01", valor_aberto: 20 }),
    ]);
    assert.equal(result.customers[0].quantidadeLinhasAbertas, 2);
    assert.equal(result.customers[0].quantidadePedidosAbertos, 2);
  });

  it("soma valor em aberto", () => {
    const result = aggregateCustomers([
      line({ valor_aberto: 100 }),
      line({ pedido: "200", valor_aberto: 25.5 }),
    ]);
    assert.equal(result.customers[0].valorTotalAberto, 125.5);
    assert.equal(result.totalValorAberto, 125.5);
  });

  it("trata valores invalidos sem NaN", () => {
    assert.equal(toFiniteNumber(null), 0);
    assert.equal(toFiniteNumber(""), 0);
    assert.equal(toFiniteNumber("x"), 0);
    assert.equal(toFiniteNumber(undefined), 0);
    const result = aggregateCustomers([
      line({ valor_aberto: /** @type {any} */ ("bad"), entregue: /** @type {any} */ (null) }),
    ]);
    assert.equal(Number.isNaN(result.customers[0].valorTotalAberto), false);
    assert.equal(result.customers[0].valorTotalAberto, 0);
  });

  it("conta pedidos atrasados sem duplicar linhas", () => {
    const result = aggregateCustomers([
      line({
        pedido: "100",
        linha: "01",
        data_entrega: "2000-01-01",
        saldo: 5,
        valor_aberto: 10,
      }),
      line({
        pedido: "100",
        linha: "02",
        data_entrega: "2000-01-02",
        saldo: 5,
        valor_aberto: 10,
      }),
      line({
        pedido: "200",
        linha: "01",
        data_entrega: "2099-01-01",
        saldo: 5,
        valor_aberto: 10,
      }),
    ]);
    assert.equal(result.customers[0].quantidadePedidosAtrasados, 1);
    assert.equal(result.customers[0].temAtraso, true);
    assert.equal(result.clientesComAtraso, 1);
  });

  it("calcula maior atraso", () => {
    const result = aggregateCustomers([
      line({ pedido: "100", data_entrega: "2000-01-10", saldo: 1, valor_aberto: 1 }),
      line({ pedido: "200", data_entrega: "2000-01-01", saldo: 1, valor_aberto: 1 }),
    ]);
    assert.ok(result.customers[0].maiorAtrasoDias >= 1);
    assert.ok(
      result.customers[0].maiorAtrasoDias >=
        result.customers[0].lines
          .map(() => 1)
          .reduce((a, b) => a + b, 0) -
          2 +
          1,
    );
  });

  it("identifica pedidos parciais", () => {
    assert.equal(isPartialDeliveryLine(line({ entregue: 2, saldo: 3 })), true);
    assert.equal(isPartialDeliveryLine(line({ entregue: 0, saldo: 3 })), false);
    assert.equal(isPartialDeliveryLine(line({ entregue: 3, saldo: 0 })), false);
    const result = aggregateCustomers([
      line({ pedido: "100", linha: "01", entregue: 2, saldo: 3 }),
      line({ pedido: "100", linha: "02", entregue: 1, saldo: 1 }),
    ]);
    assert.equal(result.customers[0].quantidadePedidosParciais, 1);
    assert.equal(result.customers[0].temPedidoParcial, true);
  });

  it("calcula proxima entrega valida", () => {
    const result = aggregateCustomers([
      line({ pedido: "100", data_entrega: "2000-01-01", saldo: 1, valor_aberto: 1 }),
      line({ pedido: "200", data_entrega: "2099-08-10", saldo: 1, valor_aberto: 1 }),
      line({ pedido: "300", data_entrega: "2099-07-01", saldo: 1, valor_aberto: 1 }),
      line({ pedido: "400", data_entrega: null, saldo: 1, valor_aberto: 1 }),
    ]);
    assert.equal(result.customers[0].proximaEntrega, "2099-07-01");
  });

  it("nao soma saldo em unidades incompativeis (sem KPI de saldo)", () => {
    const source = readFileSync(join(__dirname, "customerAggregation.ts"), "utf8");
    assert.doesNotMatch(source, /saldoTotal|quantidadeSaldo|sum\(.*saldo/i);
    const result = aggregateCustomers([
      line({ saldo: 10, valor_aberto: 1 }),
      line({ pedido: "200", saldo: 20, valor_aberto: 1 }),
    ]);
    assert.equal("saldoTotal" in result.customers[0], false);
  });

  it("contabiliza linhas com cadastro incompleto", () => {
    const result = aggregateCustomers([
      line({ codigo_cadastro: "000123", loja_cadastro: "01" }),
      line({ codigo_cadastro: "", loja_cadastro: "01", pedido: "999" }),
      line({ codigo_cadastro: "000123", loja_cadastro: "", pedido: "998" }),
    ]);
    assert.equal(result.incompleteLineCount, 2);
    assert.equal(result.customers.length, 1);
  });
});

describe("customerSorting e filters", () => {
  it("clientes atrasados aparecem primeiro", () => {
    const overdue = {
      ...aggregateCustomers([
        line({
          codigo_cadastro: "1",
          loja_cadastro: "01",
          nome_cliente: "Zeta",
          data_entrega: "2000-01-01",
          saldo: 1,
        }),
      ]).customers[0],
    };
    const ok = {
      ...aggregateCustomers([
        line({
          codigo_cadastro: "2",
          loja_cadastro: "01",
          nome_cliente: "Alpha",
          data_entrega: "2099-01-01",
          saldo: 1,
          valor_aberto: 9999,
        }),
      ]).customers[0],
    };
    const sorted = sortCustomersByAttention([ok, overdue]);
    assert.equal(sorted[0].key, overdue.key);
  });

  it("maior atraso desempata corretamente", () => {
    const a = aggregateCustomers([
      line({
        codigo_cadastro: "1",
        loja_cadastro: "01",
        data_entrega: "2000-01-10",
        saldo: 1,
        valor_aberto: 1,
      }),
    ]).customers[0];
    const b = aggregateCustomers([
      line({
        codigo_cadastro: "2",
        loja_cadastro: "01",
        data_entrega: "2000-01-01",
        saldo: 1,
        valor_aberto: 1,
      }),
    ]).customers[0];
    assert.ok(compareAttention(b, a) < 0);
  });

  it("valor em aberto participa do desempate", () => {
    const low = aggregateCustomers([
      line({
        codigo_cadastro: "1",
        loja_cadastro: "01",
        data_entrega: "2000-01-01",
        saldo: 1,
        valor_aberto: 10,
      }),
    ]).customers[0];
    const high = aggregateCustomers([
      line({
        codigo_cadastro: "2",
        loja_cadastro: "01",
        data_entrega: "2000-01-01",
        saldo: 1,
        valor_aberto: 500,
      }),
    ]).customers[0];
    const sorted = sortCustomersByAttention([low, high]);
    assert.equal(sorted[0].key, high.key);
  });

  it("busca por nome, codigo, loja e pedido", () => {
    const customer = aggregateCustomers([
      line({
        nome_cliente: "ACME Industria",
        codigo_cadastro: "000123",
        loja_cadastro: "01",
        pedido: "555",
        pedido_cliente: "PO-99",
      }),
    ]).customers[0];
    assert.equal(matchesCustomerSearch(customer, "acme"), true);
    assert.equal(matchesCustomerSearch(customer, "000123"), true);
    assert.equal(matchesCustomerSearch(customer, "01"), true);
    assert.equal(matchesCustomerSearch(customer, "555"), true);
    assert.equal(matchesCustomerSearch(customer, "PO-99"), true);
    assert.equal(matchesCustomerSearch(customer, "xyz"), false);
  });

  it("filtra atenção, inativos e crescimento pela semântica existente", () => {
    const overdue = aggregateCustomers([
      line({
        codigo_cadastro: "1",
        loja_cadastro: "01",
        data_entrega: "2000-01-01",
        saldo: 1,
        entregue: 0,
      }),
    ]).customers[0];
    const inactive = {
      ...aggregateCustomers([
      line({
        codigo_cadastro: "2",
        loja_cadastro: "01",
        data_entrega: "2099-01-01",
        saldo: 0,
        entregue: 1,
      }),
      ]).customers[0],
      status: "inativo",
    };
    const attention = { ...overdue, status: "atencao" };
    const growth = { ...overdue, key: "growth|01", status: "ativo", billingTrend: "up" };
    const customers = [attention, inactive, growth];
    assert.equal(filterCustomers(customers, "", "attention").length, 1);
    assert.equal(filterCustomers(customers, "", "inactive").length, 1);
    assert.equal(filterCustomers(customers, "", "growth").length, 1);
    assert.equal(filterCustomers(customers, "", "all").length, 3);
  });

  it("busca e filtro combinados", () => {
    const overdueAcme = aggregateCustomers([
      line({
        codigo_cadastro: "1",
        loja_cadastro: "01",
        nome_cliente: "ACME",
        data_entrega: "2000-01-01",
        saldo: 1,
      }),
    ]).customers[0];
    const overdueBeta = aggregateCustomers([
      line({
        codigo_cadastro: "2",
        loja_cadastro: "01",
        nome_cliente: "BETA",
        data_entrega: "2000-01-01",
        saldo: 1,
      }),
    ]).customers[0];
    const filtered = filterCustomers(
      [
        { ...overdueAcme, status: "atencao" },
        { ...overdueBeta, status: "atencao" },
      ],
      "acme",
      "attention",
    );
    assert.equal(filtered.length, 1);
    assert.equal(filtered[0].nome, "ACME");
  });

  it("filtra sem venda há 60 dias pelos campos reais de enrichment", () => {
    const base = aggregateCustomers([
      line({ codigo_cadastro: "1", loja_cadastro: "01" }),
    ]).customers[0];
    const recent = {
      ...base,
      key: "recent|01",
      lastPurchaseDate: new Date().toISOString().slice(0, 10),
    };
    const old = { ...base, key: "old|01", lastPurchaseDate: "2000-01-01" };
    const unknown = { ...base, key: "unknown|01", lastPurchaseDate: null };
    assert.deepEqual(
      filterCustomers([recent, old, unknown], "", "no_sale_60").map((customer) => customer.key),
      ["old|01", "unknown|01"],
    );
  });

  it("ordenacao nao muta o array original", () => {
    const original = aggregateCustomers([
      line({ codigo_cadastro: "2", loja_cadastro: "01", nome_cliente: "B" }),
      line({
        codigo_cadastro: "1",
        loja_cadastro: "01",
        nome_cliente: "A",
        data_entrega: "2000-01-01",
        saldo: 1,
      }),
    ]).customers;
    const snapshot = original.map((c) => c.key);
    sortCustomersByAttention(original);
    assert.deepEqual(
      original.map((c) => c.key),
      snapshot,
    );
  });
});

describe("CustomersPage estrutural", () => {
  it("usa getOpenOrdersTotvs e nao inventa endpoint", () => {
    const hook = readFileSync(join(__dirname, "../hooks/useCustomersData.ts"), "utf8");
    assert.match(hook, /getOpenOrdersTotvs/);
    assert.doesNotMatch(hook, /ops-abertas|getOpsAbertas/);
    assert.match(hook, /reloadKey/);
  });

  it("pagina cobre loading erro vazio e aviso incompleto", () => {
    const page = readFileSync(join(__dirname, "../pages/CustomersPage.tsx"), "utf8");
    assert.match(page, /Carregando clientes/);
    assert.match(page, /Tentar novamente/);
    assert.match(page, /identificação cadastral/);
    assert.match(page, /Nenhum cliente corresponde/);
    assert.match(page, /CustomerSummaryCards/);
    assert.doesNotMatch(page, /CustomerAttentionList/);
    assert.match(page, /CustomersTable/);
    assert.doesNotMatch(page, /clientes\/:|navigatePluginView\("customers"/);
  });

  it("usa composicao kit-first no hero, filtros, tabela desktop e cards mobile", () => {
    const page = readFileSync(join(__dirname, "../pages/CustomersPage.tsx"), "utf8");
    const table = readFileSync(join(__dirname, "../components/CustomersTable.tsx"), "utf8");
    assert.match(page, /CommercialPageHero/);
    assert.match(page, /CommercialScopeChipBar/);
    assert.match(page, /CommercialFilterBarShell/);
    assert.match(page, /SellerScopeFilter/);
    assert.match(page, /CustomerSummaryCards/);
    assert.ok(page.indexOf("CustomersTable") < page.indexOf("CustomerBillingSeriesChart"));
    for (const focus of ["all", "attention", "inactive", "growth", "no_sale_60"]) {
      assert.match(page, new RegExp(`id: "${focus}"`));
    }
    assert.match(table, /CommercialDataTable/);
    assert.match(table, /CommercialDataRecordCard/);
    assert.match(table, /onRowClick=\{openCustomer\}/);
    assert.match(table, /event\.stopPropagation\(\)/);
    assert.match(table, /href=\{detailHref\(customer\)\}/);
    assert.match(table, /commercial:customers:table-columns:v1/);
    assert.match(table, /resizableColumns/);
    assert.match(table, /enableColumnReorder/);
    assert.match(table, /CommercialTableColumnVisibilityMenu/);
    assert.doesNotMatch(table, /<table|MoreHorizontal|pva-customers-table/);
    assert.doesNotMatch(page, /@delpi\/plugin-ui/);
    assert.doesNotMatch(table, /@delpi\/plugin-ui/);
  });

  it("nao mantem componentes e CSS espelho da lista legada", () => {
    for (const file of [
      "CustomersFilters.tsx",
      "CustomerAttentionList.tsx",
      "CustomerCommercialStatus.tsx",
      "CustomerContactsStub.tsx",
    ]) {
      assert.equal(existsSync(join(__dirname, `../components/${file}`)), false);
    }
    const css = readFileSync(join(__dirname, "../../../styles/customers.css"), "utf8");
    assert.doesNotMatch(css, /pva-customers-table|pva-customers-toolbar|pva-filter-chip/);
    assert.doesNotMatch(css, /\.delpi-ui-/);
  });
});

describe("customerPortfolioKpis", () => {
  it("conta sem venda ha 60 dias e clientes ativos", async () => {
    const mod = await import("./customerPortfolioKpis.ts");
    const today = new Date("2026-08-04T12:00:00");
    assert.equal(
      mod.countCustomersWithoutSaleForDays(
        [
          { lastPurchaseDate: "2026-07-01" },
          { lastPurchaseDate: "2026-05-01" },
          { lastPurchaseDate: null },
        ],
        60,
        today,
      ),
      2,
    );
    assert.equal(
      mod.countActivePortfolioCustomers([
        { status: "ativo", quantidadePedidosAbertos: 2 },
        { status: "atencao", quantidadePedidosAbertos: 1 },
        { status: "inativo", quantidadePedidosAbertos: 0 },
        { status: "inativo", quantidadePedidosAbertos: 1 },
      ]),
      2,
    );
  });
});

describe("buildSellerNameByCustomerKey", () => {
  it("mapeia cliente ao vendedor da carteira", () => {
    const map = buildSellerNameByCustomerKey([
      {
        display_name: "Ana Silva",
        customers: [
          { customer_code: "000001", customer_store: "01", customer_name: "ACME" },
        ],
      },
      {
        display_name: "Bruno Costa",
        customers: [
          { customer_code: "000002", customer_store: "01", customer_name: "BETA" },
          { customer_code: "000001", customer_store: "01", customer_name: "ACME" },
        ],
      },
    ]);
    assert.equal(map.get("000001|01"), "Ana Silva · Bruno Costa");
    assert.equal(map.get("000002|01"), "Bruno Costa");
    assert.equal(map.has("999999|01"), false);
  });
});

describe("billingTrendPresentation", () => {
  it("formata simbolo e percentual", async () => {
    const mod = await import("./billingTrendPresentation.ts");
    assert.equal(mod.billingTrendSymbol("up"), "↑");
    assert.equal(mod.billingTrendSymbol("down"), "↓");
    assert.equal(mod.billingTrendSymbol("stable"), "→");
    assert.equal(mod.billingTrendSymbol("insufficient"), "");
    assert.match(mod.formatBillingTrendPct(10), /\+10/);
    assert.match(mod.formatBillingTrendPct(-8.5), /−|-|%/);
    assert.match(mod.billingTrendTitle("up", 12), /últimos 6 meses/);
  });
});

describe("BillingTrendCell", () => {
  it("usa icones de grafico lucide", () => {
    const src = readFileSync(
      join(__dirname, "../components/BillingTrendCell.tsx"),
      "utf8",
    );
    assert.match(src, /TrendingUp/);
    assert.match(src, /TrendingDown/);
    assert.match(src, /Minus/);
    assert.match(src, /cm-billing-trend--\$\{trend\}/);
  });
});
