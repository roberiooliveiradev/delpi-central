#!/usr/bin/env node
/**
 * Testes do faturamento no detalhe (Etapa 8) — node:test.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import {
  buildCustomerDetailSearch,
  parseCustomerDetailSection,
} from "../utils/customerDetailSection.ts";
import {
  isValidIsoDate,
  periodRangeFromPreset,
  situationLabel,
  validateBillingPeriod,
} from "../billing/utils/billingPeriod.ts";

function buildCustomerBillingPath(query) {
  const params = new URLSearchParams();
  params.set("start_date", query.startDate);
  params.set("end_date", query.endDate);
  params.set("page", String(query.page));
  params.set("page_size", String(query.pageSize));
  params.set("situation", query.situation);
  if (query.search.trim()) {
    params.set("search", query.search.trim());
  }
  return (
    `/apps/commercial-api/customers/` +
    `${encodeURIComponent(query.codigo.trim())}/` +
    `${encodeURIComponent(query.loja.trim())}/outbound-invoices?` +
    params.toString()
  );
}

const __dirname = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(__dirname, "../../..");

function readSrc(relativePath) {
  return readFileSync(join(srcRoot, relativePath), "utf8");
}

describe("customerDetailSection", () => {
  it("parseia secao da query string", () => {
    assert.equal(parseCustomerDetailSection("?secao=faturamento"), "historico");
    assert.equal(parseCustomerDetailSection("?secao=historico"), "historico");
    assert.equal(parseCustomerDetailSection("?secao=pedidos"), "pedidos");
    assert.equal(parseCustomerDetailSection(""), "resumo");
    assert.equal(parseCustomerDetailSection("?secao=x"), "resumo");
  });

  it("constroi search sem poluir resumo", () => {
    assert.equal(buildCustomerDetailSearch("resumo"), "");
    assert.equal(buildCustomerDetailSearch("historico"), "?secao=historico");
  });
});

describe("billingPeriod", () => {
  it("gera ranges de preset", () => {
    const fixed = new Date(2026, 7, 4); // 4 ago 2026
    const range = periodRangeFromPreset("90", fixed);
    assert.equal(range.endDate, "2026-08-04");
    assert.equal(range.startDate, "2026-05-07");
  });

  it("valida periodo personalizado", () => {
    assert.equal(validateBillingPeriod("2026-01-01", "2026-02-01"), null);
    assert.match(validateBillingPeriod("2026-02-01", "2026-01-01") || "", /inicial/);
    assert.equal(isValidIsoDate("2026-02-30"), false);
  });

  it("rotula situacao", () => {
    assert.equal(situationLabel("emitted"), "Emitida");
    assert.equal(situationLabel("return"), "Devolução");
  });
});

describe("customerBillingApi path", () => {
  it("preserva zeros e encoding", () => {
    const path = buildCustomerBillingPath({
      codigo: "000123",
      loja: "01",
      startDate: "2026-01-01",
      endDate: "2026-03-31",
      page: 1,
      pageSize: 20,
      situation: "all",
      search: "",
    });
    assert.match(path, /\/customers\/000123\/01\/outbound-invoices\?/);
    assert.match(path, /start_date=2026-01-01/);
    assert.doesNotMatch(path, /\/customers\/123\//);
  });

  it("nao inventa endpoint fora de commercial-api", () => {
    const path = buildCustomerBillingPath({
      codigo: "1",
      loja: "01",
      startDate: "2026-01-01",
      endDate: "2026-01-31",
      page: 1,
      pageSize: 20,
      situation: "emitted",
      search: "NF",
    });
    assert.match(path, /\/apps\/commercial-api\/customers\//);
    assert.doesNotMatch(path, /api-delpi|pedidos-venda-abertos|products\/|rol\/by-customer|fornecedor|SC7/i);
  });
});

describe("CustomerDetailPage billing (fonte)", () => {
  it("expoe navegacao secundaria e secoes", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    assert.match(page, /CustomerDetailSections/);
    assert.match(page, /historico/);
    assert.match(page, /CustomerBillingPanel/);
    assert.match(page, /useCustomerBilling/);
    assert.match(page, /useCustomerDetailData/);
    assert.match(page, /CustomerOverviewSection/);
  });

  it("mantem pedidos independentes do painel de NF", () => {
    const page = readSrc("features/customers/pages/CustomerDetailPage.tsx");
    assert.match(page, /CustomerOrdersTable|CustomerAttentionOrders/);
    assert.match(page, /resolveCustomerDetailFetchPolicy/);
    assert.match(page, /fetchPolicy\.billing/);
  });

  it("expansao acessivel na tabela de NF", () => {
    const table = readSrc(
      "features/customers/billing/components/CustomerInvoicesTable.tsx",
    );
    assert.match(table, /aria-expanded/);
    assert.match(table, /Expandir itens/);
  });

  it("cards KPI do histórico usam CommercialMetricCard", () => {
    const cards = readSrc(
      "features/customers/billing/components/CustomerBillingSummaryCards.tsx",
    );
    assert.match(cards, /CommercialMetricCard/);
    assert.match(cards, /Valor faturado no período/);
  });

  it("filtros de periodo e situacao", () => {
    const filters = readSrc(
      "features/customers/billing/components/CustomerBillingFilters.tsx",
    );
    assert.match(filters, /Últimos 90 dias/);
    assert.match(filters, /Devoluções/);
    assert.match(filters, /exclusão lógica/);
    assert.match(filters, /CommercialSegmentToggle/);
    assert.match(filters, /CommercialDateField/);
    assert.doesNotMatch(filters, /cm-nav-row|ActionButton/);
  });
});
