#!/usr/bin/env node
/**
 * Testes da resolução de rotas e navegação (sem vitest — node:test).
 * Uso: node --experimental-strip-types --test src/app/pluginRoutes.test.mjs
 *
 * Componentes React (.tsx) são validados por inspeção de fonte nesta etapa
 * (sem adicionar vitest/jsdom). A lógica de rota e navigatePluginView é executada.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it, beforeEach, afterEach } from "node:test";
import { fileURLToPath } from "node:url";

import { navigatePluginView } from "./pluginNavigation.ts";
import {
  buildPluginPath,
  isPluginNavActive,
  normalizePathname,
  PVA_BASE_PATH,
  resolvePluginRoute,
} from "./pluginRoutes.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(__dirname, "..");

function readSrc(relativePath) {
  return readFileSync(join(srcRoot, relativePath), "utf8");
}

describe("normalizePathname", () => {
  it("remove barra final", () => {
    assert.equal(normalizePathname("/apps/pedidos-venda-abertos/"), PVA_BASE_PATH);
    assert.equal(
      normalizePathname("/apps/pedidos-venda-abertos/clientes/"),
      `${PVA_BASE_PATH}/clientes`,
    );
  });

  it("ignora query string na normalização do path", () => {
    assert.equal(
      normalizePathname("/apps/pedidos-venda-abertos/clientes?x=1"),
      `${PVA_BASE_PATH}/clientes`,
    );
  });
});

describe("resolvePluginRoute", () => {
  it("rota base resolve para Pedidos em aberto (orders)", () => {
    assert.equal(resolvePluginRoute(PVA_BASE_PATH).view, "orders");
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}/`).view, "orders");
  });

  it("rota /clientes resolve para Clientes (customers)", () => {
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}/clientes`).view, "customers");
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}/clientes/`).view, "customers");
  });

  it("rota /configuracao resolve para config", () => {
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}/configuracao`).view, "config");
  });

  it("query string nao quebra a resolucao", () => {
    assert.equal(
      resolvePluginRoute(`${PVA_BASE_PATH}/clientes?tab=1`).view,
      "customers",
    );
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}?foo=bar`).view, "orders");
  });

  it("rota interna desconhecida exibe fallback not_found", () => {
    assert.equal(resolvePluginRoute(`${PVA_BASE_PATH}/invalida`).view, "not_found");
    assert.equal(
      resolvePluginRoute(`${PVA_BASE_PATH}/clientes/001`).view,
      "not_found",
    );
    assert.equal(
      resolvePluginRoute(`${PVA_BASE_PATH}/clientes/001/01/extra`).view,
      "not_found",
    );
  });

  it("rota /clientes/:codigo/:loja resolve para customer_detail", () => {
    const route = resolvePluginRoute(`${PVA_BASE_PATH}/clientes/000123/01`);
    assert.equal(route.view, "customer_detail");
    assert.equal(route.codigo, "000123");
    assert.equal(route.loja, "01");
  });
});

describe("isPluginNavActive / buildPluginPath", () => {
  it("aba ativa corresponde a rota", () => {
    assert.equal(isPluginNavActive("orders", "orders"), true);
    assert.equal(isPluginNavActive("orders", "customers"), false);
    assert.equal(isPluginNavActive("customers", "customers"), true);
    assert.equal(isPluginNavActive("customer_detail", "customers"), true);
    assert.equal(isPluginNavActive("customer_detail", "orders"), false);
    assert.equal(isPluginNavActive("not_found", "orders"), false);
  });

  it("buildPluginPath preserva search quando informado", () => {
    assert.equal(buildPluginPath("orders"), PVA_BASE_PATH);
    assert.equal(buildPluginPath("customers"), `${PVA_BASE_PATH}/clientes`);
    assert.equal(
      buildPluginPath("customers", PVA_BASE_PATH, "?q=1"),
      `${PVA_BASE_PATH}/clientes?q=1`,
    );
  });
});

describe("navigatePluginView", () => {
  /** @type {string[]} */
  let pushed = [];
  /** @type {string[]} */
  let events = [];
  const originalWindow = globalThis.window;

  beforeEach(() => {
    pushed = [];
    events = [];
    globalThis.PopStateEvent = class PopStateEvent extends Event {
      constructor(type = "popstate") {
        super(type);
      }
    };
    globalThis.window = {
      location: {
        pathname: PVA_BASE_PATH,
        search: "",
      },
      history: {
        pushState: (_state, _title, url) => {
          pushed.push(String(url));
          const [path, query = ""] = String(url).split("?");
          globalThis.window.location.pathname = path;
          globalThis.window.location.search = query ? `?${query}` : "";
        },
      },
      dispatchEvent: (event) => {
        events.push(event.type);
        return true;
      },
    };
  });

  afterEach(() => {
    globalThis.window = originalWindow;
  });

  it("clique em Clientes navega para /clientes", () => {
    navigatePluginView("customers");
    assert.deepEqual(pushed, [`${PVA_BASE_PATH}/clientes`]);
    assert.deepEqual(events, ["popstate"]);
  });

  it("clique em Pedidos em aberto retorna a rota base", () => {
    globalThis.window.location.pathname = `${PVA_BASE_PATH}/clientes`;
    navigatePluginView("orders");
    assert.deepEqual(pushed, [PVA_BASE_PATH]);
    assert.deepEqual(events, ["popstate"]);
  });

  it("nao empurha historico se ja estiver na mesma rota", () => {
    navigatePluginView("orders");
    assert.deepEqual(pushed, []);
    assert.deepEqual(events, []);
  });
});

describe("App shell e paginas (fonte)", () => {
  it("App monta Pedidos, Clientes, detalhe e fallback", () => {
    const app = readSrc("App.tsx");
    assert.match(app, /view === "orders" \? <PedidosVendaAbertosPage/);
    assert.match(app, /view === "customers" \? <CustomersPage/);
    assert.match(app, /view === "config" \? <SellerConfigPage/);
    assert.match(app, /view === "customer_detail"/);
    assert.match(app, /CustomerDetailPage/);
    assert.match(app, /view === "not_found" \? <NotFoundPage/);
    assert.match(app, /PortfolioScopeProvider/);
  });

  it("PluginNav expoe abas acessiveis por teclado", () => {
    const nav = readSrc("app/PluginNav.tsx");
    assert.match(nav, /role="tablist"/);
    assert.match(nav, /role="tab"/);
    assert.match(nav, /aria-selected/);
    assert.match(nav, /aria-current/);
    assert.match(nav, /ArrowRight/);
    assert.match(nav, /ArrowLeft/);
    assert.match(nav, /Pedidos em aberto/);
    assert.match(nav, /Minha carteira/);
    assert.match(nav, /navigatePluginView/);
    assert.match(nav, /showConfig/);
    assert.match(nav, /Configuração/);
  });

  it("SellerConfigPage busca clientes ativos TOTVS", () => {
    const page = readSrc("features/customers/pages/SellerConfigPage.tsx");
    assert.match(page, /searchActiveTotvsCustomers/);
    assert.match(page, /Buscar cliente ativo/);
    assert.match(page, /term\.length < 2/);
    assert.match(page, /Adicionar do TOTVS/);
    assert.match(page, /Vinculados/);
    assert.match(page, /transferSellerCustomers/);
    assert.match(page, /Transferir/);
    assert.match(page, /outro vendedor ativo/);
    assert.match(page, /upsertCustomerAvatar/);
    const api = readSrc("api/sellerPortfolioApi.ts");
    assert.match(api, /\/customers\/search/);
    assert.match(api, /\/customers\/transfer/);
  });

  it("CustomersTable usa colunas do mockup e enrichment", () => {
    const table = readSrc("features/customers/components/CustomersTable.tsx");
    assert.match(table, /CustomerAvatar/);
    assert.match(table, /Cidade \/ UF/);
    assert.match(table, /Faturamento 12 meses/);
    assert.match(table, /Última venda/);
    assert.doesNotMatch(table, /Última compra/);
    assert.doesNotMatch(table, /Próxima ação/);
    assert.match(table, /Vendedor/);
    assert.match(table, /sellerName/);
    assert.match(table, /billingTrend/);
    assert.match(table, /Tendência/);
    assert.match(table, /BillingTrendCell/);
    assert.match(table, /HelpTooltip/);
    assert.match(table, /BILLING_TREND_HELP/);
    const help = readSrc("features/customers/utils/billingTrendPresentation.ts");
    assert.match(help, /BILLING_TREND_HELP/);
    assert.match(help, /últimos 6 meses/);
    assert.match(help, /5%/);
    assert.match(help, /alta \(verde\)/);
    assert.doesNotMatch(help, /deadband|billing_trend|semestre recente|H2|CRM/);
    const helpConst = help.match(/export const BILLING_TREND_HELP[\s\S]*?;/);
    assert.ok(helpConst);
    assert.doesNotMatch(helpConst[0], /insufficient|deadband|billing_trend/);
    const trendCell = readSrc("features/customers/components/BillingTrendCell.tsx");
    assert.match(trendCell, /TrendingUp/);
    assert.match(trendCell, /TrendingDown/);
    assert.match(trendCell, /Minus/);
    assert.match(trendCell, /pva-billing-trend/);
    const api = readSrc("api/customerEnrichmentApi.ts");
    assert.match(api, /\/customers\/enrichment/);
    assert.match(api, /billing_trend/);
  });

  it("CustomersPage inclui gráfico de faturamento 12m", () => {
    const page = readSrc("features/customers/pages/CustomersPage.tsx");
    assert.match(page, /CustomerBillingSeriesChart/);
    const chart = readSrc("features/customers/components/CustomerBillingSeriesChart.tsx");
    assert.match(chart, /from \"recharts\"/);
    assert.match(chart, /ResponsiveContainer/);
    assert.match(chart, /AreaChart/);
    assert.match(chart, /Faturamento — últimos 12 meses/);
    assert.doesNotMatch(chart, /ConfigurableSeriesChart|ComparativeAreaChart/);
    const api = readSrc("api/customerBillingSeriesApi.ts");
    assert.match(api, /\/customers\/billing-series/);
  });

  it("CustomerDetailPage segue mockup de visão geral", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    assert.match(page, /CustomerOverviewSection/);
    assert.match(page, /CustomerDetailHeader/);
    const overview = readSrc("features/customers/components/CustomerOverviewSection.tsx");
    assert.match(overview, /CustomerPurchaseEvolutionChart/);
    assert.match(overview, /CustomerOpenOrdersPreview/);
    assert.match(overview, /CustomerNextActionCard/);
    assert.match(overview, /CustomerContactsStub/);
  });

  it("CustomersPage resolve vendedor da carteira", () => {
    const page = readSrc("features/customers/pages/CustomersPage.tsx");
    assert.match(page, /buildSellerNameByCustomerKey/);
    assert.match(page, /sellerNameByKey/);
    assert.match(page, /myPortfolio/);
  });

  it("CustomersPage renderiza titulo e nao dispara API", () => {
    const page = readSrc("features/customers/pages/CustomersPage.tsx");
    assert.match(page, /pva-internal-page__title">Minha carteira de clientes</);
    assert.match(page, /Clientes da sua carteira com pedidos de venda em aberto/);
    assert.doesNotMatch(page, /httpGet|httpClient|fetch\(|pedidosVendaAbertosApi|api-delpi/);
    assert.doesNotMatch(page, /em breve/i);
  });

  it("NotFoundPage fallback oferecee Clientes e Pedidos", () => {
    const page = readSrc("app/NotFoundPage.tsx");
    assert.match(page, /Página não encontrada|Pagina nao encontrada/);
    assert.match(page, /navigatePluginView\("customers"/);
    assert.match(page, /navigatePluginView\("orders"/);
  });
});
