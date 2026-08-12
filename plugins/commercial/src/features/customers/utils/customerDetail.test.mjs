#!/usr/bin/env node
/**
 * Testes do detalhe do cliente (Etapa 5) — node:test, sem vitest.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it, beforeEach, afterEach } from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildCustomerDetailPath,
  navigateCustomerDetail,
} from "../../../app/pluginNavigation.ts";
import {
  COMMERCIAL_BASE_PATH,
  isPluginNavActive,
  resolvePluginRoute,
} from "../../../app/pluginRoutes.ts";
import { aggregateCustomers } from "./customerAggregation.ts";
import { buildCommercialStatusLines } from "./customerCommercialStatus.ts";
import { findCustomerByIdentity } from "./customerLookup.ts";
import {
  aggregateCustomerOrders,
  pickPedidoCliente,
  selectAttentionOrders,
} from "./customerOrderAggregation.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(__dirname, "../../..");

function readSrc(relativePath) {
  return readFileSync(join(srcRoot, relativePath), "utf8");
}

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

describe("resolvePluginRoute — customer_detail", () => {
  it("reconhece /customers/:codigo/:loja", () => {
    const route = resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000123/01`);
    assert.equal(route.view, "customer_detail");
    assert.equal(route.codigo, "000123");
    assert.equal(route.loja, "01");
  });

  it("preserva zeros a esquerda", () => {
    const route = resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000123/01`);
    assert.equal(route.codigo, "000123");
    assert.notEqual(route.codigo, "123");
  });

  it("decodifica segmentos", () => {
    const route = resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000%20123/0%201`);
    assert.equal(route.view, "customer_detail");
    assert.equal(route.codigo, "000 123");
    assert.equal(route.loja, "0 1");
  });

  it("trata encoding invalido", () => {
    assert.equal(
      resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/%E0%A4%A/01`).view,
      "not_found",
    );
  });

  it("rejeita segmentos extras", () => {
    assert.equal(
      resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000123/01/extra`).view,
      "not_found",
    );
  });

  it("aceita barra final", () => {
    assert.equal(
      resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000123/01/`).view,
      "customer_detail",
    );
  });

  it("ignora query string", () => {
    const route = resolvePluginRoute(`${COMMERCIAL_BASE_PATH}/customers/000123/01?x=1`);
    assert.equal(route.view, "customer_detail");
    assert.equal(route.codigo, "000123");
  });

  it("mantem aba Clientes ativa no detalhe", () => {
    assert.equal(isPluginNavActive("customer_detail", "customers"), true);
    assert.equal(isPluginNavActive("customer_detail", "orders"), false);
  });
});

describe("buildCustomerDetailPath", () => {
  it("constroi path com encoding seguro", () => {
    assert.equal(
      buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "000123", "01"),
      `${COMMERCIAL_BASE_PATH}/customers/000123/01`,
    );
    assert.equal(
      buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "a/b", "01"),
      `${COMMERCIAL_BASE_PATH}/customers/a%2Fb/01`,
    );
  });

  it("rejeita codigo vazio", () => {
    assert.equal(buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "", "01"), null);
    assert.equal(buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "   ", "01"), null);
  });

  it("rejeita loja vazia", () => {
    assert.equal(buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "000123", ""), null);
    assert.equal(buildCustomerDetailPath(COMMERCIAL_BASE_PATH, "000123", "  "), null);
  });
});

describe("findCustomerByIdentity", () => {
  const { customers } = aggregateCustomers([
    line({ codigo_cadastro: "000123", loja_cadastro: "01", nome_cliente: "ACME" }),
    line({
      codigo_cadastro: "000123",
      loja_cadastro: "02",
      nome_cliente: "ACME LOJA 2",
      pedido: "200",
    }),
  ]);

  it("encontra cliente por codigo e loja", () => {
    const found = findCustomerByIdentity(customers, "000123", "01");
    assert.ok(found);
    assert.equal(found.nome, "ACME");
  });

  it("nao encontra por nome", () => {
    assert.equal(findCustomerByIdentity(customers, "ACME", "01"), null);
  });

  it("nao mistura lojas", () => {
    const found = findCustomerByIdentity(customers, "000123", "02");
    assert.ok(found);
    assert.equal(found.loja, "02");
    assert.notEqual(found.key, findCustomerByIdentity(customers, "000123", "01")?.key);
  });

  it("nao converte identificadores para numero", () => {
    const withZeros = aggregateCustomers([
      line({ codigo_cadastro: "000123", loja_cadastro: "01" }),
      line({ codigo_cadastro: "123", loja_cadastro: "01", pedido: "999" }),
    ]).customers;
    assert.equal(findCustomerByIdentity(withZeros, "000123", "01")?.codigo, "000123");
    assert.equal(findCustomerByIdentity(withZeros, "123", "01")?.codigo, "123");
    assert.notEqual(
      findCustomerByIdentity(withZeros, "000123", "01")?.key,
      findCustomerByIdentity(withZeros, "123", "01")?.key,
    );
  });

  it("nao muta lista", () => {
    const snapshot = customers.map((c) => c.key);
    findCustomerByIdentity(customers, "000123", "01");
    assert.deepEqual(
      customers.map((c) => c.key),
      snapshot,
    );
  });
});

describe("aggregateCustomerOrders", () => {
  it("agrupa linhas por filial e pedido", () => {
    const orders = aggregateCustomerOrders([
      line({ pedido: "100", linha: "01", valor_aberto: 50 }),
      line({ pedido: "100", linha: "02", valor_aberto: 25 }),
      line({ pedido: "200", linha: "01", valor_aberto: 10 }),
    ]);
    assert.equal(orders.length, 2);
    const p100 = orders.find((o) => o.pedido === "100");
    assert.equal(p100?.quantidadeLinhas, 2);
    assert.equal(p100?.valorTotalAberto, 75);
  });

  it("separa filiais diferentes", () => {
    const orders = aggregateCustomerOrders([
      line({ filial: "01", pedido: "100" }),
      line({ filial: "02", pedido: "100" }),
    ]);
    assert.equal(orders.length, 2);
  });

  it("preserva zeros", () => {
    const orders = aggregateCustomerOrders([
      line({ filial: "01", pedido: "000100" }),
    ]);
    assert.equal(orders[0]?.pedido, "000100");
  });

  it("soma valor com seguranca", () => {
    const orders = aggregateCustomerOrders([
      line({ valor_aberto: "10" }),
      line({ pedido: "100", linha: "02", valor_aberto: null }),
      line({ pedido: "100", linha: "03", valor_aberto: "x" }),
    ]);
    assert.equal(orders[0]?.valorTotalAberto, 10);
  });

  it("conta linhas", () => {
    const orders = aggregateCustomerOrders([
      line({ linha: "01" }),
      line({ linha: "02", pedido: "100" }),
    ]);
    assert.equal(orders[0]?.quantidadeLinhas, 2);
  });

  it("identifica atraso e maior atraso", () => {
    const orders = aggregateCustomerOrders([
      line({ data_entrega: "2000-01-01", saldo: 5, valor_aberto: 10 }),
      line({
        pedido: "100",
        linha: "02",
        data_entrega: "1999-01-01",
        saldo: 5,
        valor_aberto: 10,
      }),
    ]);
    assert.equal(orders[0]?.temAtraso, true);
    assert.ok((orders[0]?.maiorAtrasoDias ?? 0) > 0);
    assert.equal(orders[0]?.situacao, "atrasado");
  });

  it("identifica parcialidade", () => {
    const orders = aggregateCustomerOrders([
      line({ entregue: 2, saldo: 8, data_entrega: "2099-01-01" }),
    ]);
    assert.equal(orders[0]?.temParcial, true);
    assert.equal(orders[0]?.situacao, "parcial");
  });

  it("calcula proxima entrega", () => {
    const orders = aggregateCustomerOrders([
      line({ data_entrega: "2099-12-01", saldo: 1 }),
      line({ pedido: "100", linha: "02", data_entrega: "2099-06-01", saldo: 1 }),
    ]);
    assert.equal(orders[0]?.proximaEntrega, "2099-06-01");
  });

  it("escolhe pedido_cliente deterministicamente", () => {
    assert.equal(
      pickPedidoCliente([
        line({ pedido_cliente: "" }),
        line({ pedido_cliente: "PO-A" }),
        line({ pedido_cliente: "PO-B" }),
      ]),
      "PO-A",
    );
  });

  it("mantem referencias imutaveis as linhas", () => {
    const lines = [line()];
    const orders = aggregateCustomerOrders(lines);
    assert.equal(orders[0]?.lines[0], lines[0]);
  });
});

describe("selectAttentionOrders", () => {
  const overdueHigh = {
    ...aggregateCustomerOrders([
      line({
        pedido: "300",
        data_entrega: "1990-01-01",
        saldo: 1,
        valor_aberto: 50,
      }),
    ])[0],
  };
  const overdueLow = {
    ...aggregateCustomerOrders([
      line({
        pedido: "200",
        data_entrega: "2000-01-01",
        saldo: 1,
        valor_aberto: 200,
      }),
    ])[0],
  };
  const partial = {
    ...aggregateCustomerOrders([
      line({
        pedido: "100",
        entregue: 1,
        saldo: 1,
        data_entrega: "2099-01-01",
        valor_aberto: 10,
      }),
    ])[0],
  };
  const nextOnly = {
    ...aggregateCustomerOrders([
      line({
        pedido: "400",
        data_entrega: "2099-03-01",
        saldo: 1,
        valor_aberto: 5,
      }),
    ])[0],
  };

  it("atrasados vem primeiro e maior atraso ordena", () => {
    const input = [partial, overdueLow, overdueHigh];
    const result = selectAttentionOrders(input, null);
    assert.equal(result[0]?.pedido, "300");
    assert.equal(result[1]?.pedido, "200");
    assert.equal(result[2]?.pedido, "100");
  });

  it("valor participa do desempate entre atrasados", () => {
    const a = {
      ...aggregateCustomerOrders([
        line({ pedido: "10", data_entrega: "2000-01-01", saldo: 1, valor_aberto: 10 }),
      ])[0],
    };
    const b = {
      ...aggregateCustomerOrders([
        line({ pedido: "20", data_entrega: "2000-01-01", saldo: 1, valor_aberto: 90 }),
      ])[0],
    };
    const result = selectAttentionOrders([a, b], null);
    assert.equal(result[0]?.pedido, "20");
  });

  it("parciais nao atrasados vem depois", () => {
    const result = selectAttentionOrders([partial, overdueLow], null);
    assert.equal(result[0]?.temAtraso, true);
    assert.equal(result[1]?.temParcial, true);
  });

  it("proxima entrega nao duplica pedido ja destacado", () => {
    const result = selectAttentionOrders([partial], "2099-01-01");
    assert.equal(result.length, 1);
    assert.equal(result[0]?.pedido, "100");
  });

  it("proxima entrega destaca pedido ainda nao listado", () => {
    const result = selectAttentionOrders([partial, nextOnly], "2099-03-01");
    assert.equal(result.length, 2);
    assert.equal(result[1]?.pedido, "400");
  });

  it("ordenacao nao muta entrada", () => {
    const input = [partial, overdueLow];
    const keys = input.map((o) => o.key);
    selectAttentionOrders(input, null);
    assert.deepEqual(
      input.map((o) => o.key),
      keys,
    );
  });
});

describe("buildCommercialStatusLines", () => {
  it("produz linhas objetivas", () => {
    const customer = aggregateCustomers([
      line({ data_entrega: "2000-01-01", saldo: 1 }),
    ]).customers[0];
    const lines = buildCommercialStatusLines(customer);
    assert.ok(lines.some((l) => l.includes("atrasados")));
  });
});

describe("CustomerDetailPage e navegacao (fonte)", () => {
  it("App monta customer_detail", () => {
    const app = readSrc("App.tsx");
    assert.match(app, /view === "customer_detail"/);
    assert.match(app, /CustomerDetailPage/);
    assert.doesNotMatch(app, /ops-abertas|faturamento|nota.?fiscal/i);
  });

  it("pagina cobre loading, erro, nao encontrado e retorno", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    assert.match(page, /Carregando dados do cliente/);
    assert.match(page, /Tentar novamente/);
    assert.match(page, /Cliente fora da carteira/);
    assert.match(page, /não está nas suas carteiras/);
    assert.match(page, /buildCustomersListPath/);
    assert.match(page, /navigatePluginPath/);
    assert.match(page, /useCustomerDetailData/);
    assert.match(page, /CustomerOverviewSection/);
    assert.match(page, /CustomerDetailHeader/);
    assert.doesNotMatch(page, /httpGet|fetch\(/);
  });

  it("abas do mockup e aliases de secao", async () => {
    const {
      parseCustomerDetailSection,
      buildCustomerDetailSearch,
      customerDetailPanelId,
      customerDetailTabId,
    } = await import("./customerDetailSection.ts");
    assert.equal(parseCustomerDetailSection(""), "resumo");
    assert.equal(parseCustomerDetailSection("?secao=faturamento"), "historico");
    assert.equal(parseCustomerDetailSection("?secao=historico"), "historico");
    assert.equal(parseCustomerDetailSection("?secao=contatos"), "atividades");
    assert.equal(parseCustomerDetailSection("?secao=atividades"), "atividades");
    assert.equal(buildCustomerDetailSearch("resumo"), "");
    assert.equal(buildCustomerDetailSearch("historico"), "?secao=historico");
    assert.equal(customerDetailTabId("atividades"), "customer-tab-atividades");
    assert.equal(customerDetailPanelId("atividades"), "customer-panel-atividades");
    const sections = readSrc("features/customers/components/CustomerDetailSections.tsx");
    assert.match(sections, /Visão geral/);
    assert.match(sections, /Histórico de vendas/);
    assert.match(sections, /Oportunidades/);
    assert.match(sections, /CommercialUnderlineNav/);
    assert.match(sections, /mode="tabs"/);
    assert.match(sections, /customerDetailPanelId/);
    assert.match(sections, /openOrdersCount/);
  });

  it("condiciona fontes secundárias à aba e ao RBAC", async () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    const overview = readSrc("features/customers/components/CustomerOverviewSection.tsx");
    const activitiesHook = readSrc("features/customers/hooks/useCustomerActivities.ts");
    const { resolveCustomerDetailFetchPolicy } = await import("./customerDetailSection.ts");
    assert.deepEqual(
      resolveCustomerDetailFetchPolicy({
        section: "resumo",
        hasCustomer: true,
        canViewWorklist: true,
      }),
      { billing: false, activities: true },
    );
    assert.deepEqual(
      resolveCustomerDetailFetchPolicy({
        section: "historico",
        hasCustomer: true,
        canViewWorklist: true,
      }),
      { billing: true, activities: false },
    );
    assert.deepEqual(
      resolveCustomerDetailFetchPolicy({
        section: "atividades",
        hasCustomer: true,
        canViewWorklist: false,
      }),
      { billing: false, activities: false },
    );
    assert.deepEqual(
      resolveCustomerDetailFetchPolicy({
        section: "historico",
        hasCustomer: false,
        canViewWorklist: true,
      }),
      { billing: false, activities: false },
    );
    assert.match(page, /resolveCustomerDetailFetchPolicy/);
    assert.match(page, /useCustomerBilling\(codigo, loja, fetchPolicy\.billing\)/);
    assert.match(page, /fetchPolicy\.activities/);
    assert.match(overview, /useCustomerPurchaseEvolution/);
    assert.match(overview, /CustomerPurchaseEvolutionChart/);
    assert.match(overview, /CustomerActivityTimelinePanel/);
    assert.match(overview, /preview/);
    assert.doesNotMatch(overview, /listCustomerActivities/);
    assert.match(activitiesHook, /if \(!enabled\)/);
    assert.match(activitiesHook, /AbortController/);
    assert.match(activitiesHook, /reload/);
  });

  it("overview usa pontos factuais e mantém próxima ação somente no hero", () => {
    const overview = readSrc("features/customers/components/CustomerOverviewSection.tsx");
    const points = readSrc("features/customers/components/CustomerConversationPoints.tsx");
    const header = readSrc("features/customers/components/CustomerDetailHeader.tsx");
    assert.match(overview, /CustomerConversationPoints/);
    assert.doesNotMatch(overview, /CustomerAttentionBanner|CustomerNextActionCard|CustomerOverviewKpis/);
    assert.match(points, /Pontos para conversa/);
    assert.match(points, /CommercialStatusBadge/);
    assert.match(points, /Nenhum ponto objetivo identificado/);
    assert.match(header, /Próxima ação:/);
    assert.match(header, /buildCustomerHeroHighlights/);
  });

  it("header oferece atualização direta sem duplicar menu", () => {
    const header = readSrc("features/customers/components/CustomerDetailHeader.tsx");
    assert.match(header, /Atualizar seção/);
    assert.match(header, /onClick=\{onReload\}/);
    assert.doesNotMatch(header, /Mais ações|menuOpen|MoreHorizontal/);
  });

  it("CTAs da conta respeitam identidade e permissoes reais", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    const header = readSrc("features/customers/components/CustomerDetailHeader.tsx");
    const opportunities = readSrc(
      "features/customers/components/CustomerOpportunitiesSection.tsx",
    );
    const lines = readSrc("features/customers/components/CustomerOrderLines.tsx");
    assert.match(page, /canViewWorklist && canManageFollowups/);
    assert.doesNotMatch(header, /Registrar contato|onRegisterContact/);
    assert.match(page, /CustomerOpportunitiesSection/);
    assert.match(opportunities, /getCommercialProposals/);
    assert.match(opportunities, /CommercialProposalsTable/);
    assert.match(opportunities, /canViewAnalytics/);
    assert.match(lines, /line\.filial.*line\.pedido.*line\.linha/s);
    assert.match(lines, /getLineOpForecast/);
    assert.match(lines, /navigateOpenOrderOpDetail/);
    assert.match(lines, /canViewAnalytics && proposalNumber/);
    assert.match(lines, /navigateAnalyticsOpportunityDetail/);
    assert.match(lines, /Ver OV \{proposalNumber\}/);
    assert.match(lines, /buildOpenOrdersContextSearch/);
    assert.match(header, /canViewProposals/);
    assert.match(header, /Propostas gerais/);
    assert.doesNotMatch(header, /Ver pedidos/);
    assert.doesNotMatch(page, /CustomerAccountRail|cm-customer-overview__grid/);
    assert.doesNotMatch(page, /iframe|dashboard-production|production-appointments/);
  });

  it("hero da conta substitui o rail flutuante", () => {
    const header = readSrc("features/customers/components/CustomerDetailHeader.tsx");
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    const css = readSrc("styles/customers.css");
    assert.match(header, /CommercialPageHero/);
    assert.match(header, /CommercialPagePath/);
    assert.doesNotMatch(page, /cm-customer-account-rail/);
    assert.doesNotMatch(css, /cm-customer-account-rail-slot--desktop/);
    assert.match(css, /@media \(max-width: 768px\)/);
  });

  it("usa PagePath inclusive sem customer e tabpanel rotulado", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    const header = readSrc("features/customers/components/CustomerDetailHeader.tsx");
    assert.match(header, /<CommercialPagePath/);
    assert.match(page, /notFound=\{notFound\}/);
    assert.doesNotMatch(page, /detail-breadcrumb/);
    assert.match(page, /role="tabpanel"/);
    assert.match(page, /aria-labelledby=\{customerDetailTabId\(section\)\}/);
  });

  it("pedidos usam DataTable, cards e expansao acessivel", () => {
    const table = readSrc("features/customers/components/CustomerOrdersTable.tsx");
    const preview = readSrc("features/customers/components/CustomerOpenOrdersPreview.tsx");
    assert.match(table, /CommercialDataTable/);
    assert.match(table, /CommercialDataRecordCard/);
    assert.match(table, /aria-expanded/);
    assert.match(table, /aria-controls/);
    assert.match(table, /Expandir linhas/);
    assert.match(table, /findFirstNavigableOrderLine/);
    assert.match(table, /Abrir pedido/);
    assert.match(table, /navigateOpenOrderLineDetail/);
    assert.match(preview, /navigateOpenOrderLineDetail/);
    assert.match(preview, /Abrir linha/);
    assert.match(preview, /canViewAnalytics \? findOrderProposalLine/);
    assert.match(preview, /navigateAnalyticsOpportunityDetail/);
    assert.match(preview, /Ver OV \{proposalNumber\}/);
    assert.doesNotMatch(`${table}\n${preview}`, /Modal|Workbench/);
  });

  it("navegacao a partir da tabela de clientes", () => {
    const table = readSrc("features/customers/components/CustomersTable.tsx");
    const card = readSrc("features/customers/components/CustomerListCard.tsx");
    assert.match(table, /navigateCustomerDetail/);
    assert.match(table, /CustomerListCard/);
    assert.match(table, /CommercialInteractiveDataCard|onOpenDetail=\{openCustomer\}/);
    assert.match(card, /CommercialInteractiveDataCard/);
    assert.match(card, /CM_HELP\.customers\.cardAriaOpen/);
    assert.match(card, /onActivate=\{openDetail\}/);
  });

  it("nenhuma API nova no detalhe", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    const hook = readSrc("features/customers/hooks/useCustomerDetailData.ts");
    assert.match(hook, /useCustomersData/);
    assert.doesNotMatch(page, /getOpsAbertas|ops-abertas/);
    assert.doesNotMatch(hook, /getOpsAbertas|ops-abertas/);
  });

  it("hook de dados nao depende da pagina de lista", () => {
    const hook = readSrc("features/customers/hooks/useCustomerDetailData.ts");
    assert.doesNotMatch(hook, /CustomersPage/);
  });

  it("oportunidades hidrata busca da URL e mantém retorno", () => {
    const page = readSrc("features/analytics/AnalyticsOpportunitiesPage.tsx");
    assert.match(page, /useState\(\(\) => readAnalyticsOpportunitySearch\(\)\)/);
    assert.match(page, /subscribeAnalyticsFilterRouteSync/);
    assert.match(page, /writeAnalyticsOpportunitySearchToUrl\(search\)/);
    assert.match(page, /buildAnalyticsOpportunityBackSearch\(\)/);
  });
});

describe("navigateCustomerDetail", () => {
  /** @type {string[]} */
  let pushed = [];
  const originalWindow = globalThis.window;

  beforeEach(() => {
    pushed = [];
    globalThis.PopStateEvent = class PopStateEvent extends Event {
      constructor(type = "popstate") {
        super(type);
      }
    };
    globalThis.window = {
      location: { pathname: `${COMMERCIAL_BASE_PATH}/customers`, search: "" },
      history: {
        pushState: (_s, _t, url) => {
          pushed.push(String(url));
        },
      },
      dispatchEvent: () => true,
    };
  });

  afterEach(() => {
    globalThis.window = originalWindow;
  });

  it("navega para detalhe com encoding", () => {
    assert.equal(navigateCustomerDetail("000123", "01"), true);
    assert.deepEqual(pushed, [`${COMMERCIAL_BASE_PATH}/customers/000123/01`]);
  });

  it("preserva somente query allowlisted e seller permitido", () => {
    assert.equal(
      navigateCustomerDetail("000123", "01", {
        search:
          "?q=Acme&focus=no_sale_60&trend=down&seller_id=seller-1&redirect=https://example.com",
        sellerAccess: {
          allowSellerId: true,
          validSellerIds: ["seller-1"],
        },
      }),
      true,
    );
    assert.deepEqual(pushed, [
      `${COMMERCIAL_BASE_PATH}/customers/000123/01?q=Acme&focus=no_sale_60&trend=down&seller_id=seller-1`,
    ]);
  });

  it("remove seller sem RBAC ou fora do escopo válido", () => {
    assert.equal(
      navigateCustomerDetail("000123", "01", {
        search: "?focus=attention&seller_id=seller-1",
      }),
      true,
    );
    assert.deepEqual(pushed, [
      `${COMMERCIAL_BASE_PATH}/customers/000123/01?focus=attention`,
    ]);
  });

  it("recusa identidade incompleta", () => {
    assert.equal(navigateCustomerDetail("", "01"), false);
    assert.deepEqual(pushed, []);
  });
});
