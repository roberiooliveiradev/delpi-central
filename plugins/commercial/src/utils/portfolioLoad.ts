/**
 * Helpers para consumir GET /seller-portfolios/load-summary (E6.2).
 */
import { PORTFOLIO_LOAD_CONTENT } from "../content/portfolioLoadContent";
import type {
  PersonLoadItem,
  PortfolioLoadItem,
  SellerPortfoliosLoadSummary,
} from "../types/portfolio";

export function portfolioLoadById(
  summary: SellerPortfoliosLoadSummary | null | undefined,
): Map<string, PortfolioLoadItem> {
  const map = new Map<string, PortfolioLoadItem>();
  for (const item of summary?.portfolios ?? []) {
    if (item.id) map.set(item.id, item);
  }
  return map;
}

export function personLoadByUserId(
  summary: SellerPortfoliosLoadSummary | null | undefined,
): Map<string, PersonLoadItem> {
  const map = new Map<string, PersonLoadItem>();
  for (const item of summary?.by_person ?? []) {
    if (item.user_id) map.set(item.user_id, item);
  }
  return map;
}

export function resolvePortfolioLoad(
  summary: SellerPortfoliosLoadSummary | null | undefined,
  portfolioId: string,
  fallback?: { customer_count?: number; member_count?: number },
): PortfolioLoadItem {
  const found = portfolioLoadById(summary).get(portfolioId);
  if (found) return found;
  return {
    id: portfolioId,
    display_name: "",
    active: true,
    customer_count: fallback?.customer_count ?? 0,
    member_count: fallback?.member_count ?? 0,
    open_value: null,
    attention_count: null,
  };
}

/** Compacta valores grandes: R$ 1,7 mi / R$ 850 mil / R$ 1.234,56 */
export function formatCompactOpenValue(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return PORTFOLIO_LOAD_CONTENT.openValueUnavailable;
  }
  const abs = Math.abs(value);
  if (abs >= 1_000_000) {
    const mi = value / 1_000_000;
    return `R$ ${mi.toLocaleString("pt-BR", {
      maximumFractionDigits: 1,
      minimumFractionDigits: 0,
    })} mi`;
  }
  if (abs >= 1_000) {
    const mil = value / 1_000;
    return `R$ ${mil.toLocaleString("pt-BR", {
      maximumFractionDigits: 0,
    })} mil`;
  }
  return value.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export function formatCustomerCountShort(count: number): string {
  return `${count.toLocaleString("pt-BR")} ${PORTFOLIO_LOAD_CONTENT.customersShort}`;
}

export function formatMemberCountShort(count: number): string {
  return `${count.toLocaleString("pt-BR")} ${PORTFOLIO_LOAD_CONTENT.membersShort}`;
}

export function formatPortfolioCountShort(count: number): string {
  return `${count.toLocaleString("pt-BR")} ${PORTFOLIO_LOAD_CONTENT.portfoliosShort}`;
}

export function formatAttentionCount(count: number | null | undefined): string {
  if (count === null || count === undefined) {
    return `${PORTFOLIO_LOAD_CONTENT.attentionLabel} ${PORTFOLIO_LOAD_CONTENT.attentionUnavailable}`;
  }
  return `${PORTFOLIO_LOAD_CONTENT.attentionLabel} ${count.toLocaleString("pt-BR")}`;
}

/** Linha compacta: `5 cli · R$ 1,7 mi · Atenção 4 · 2 membros` */
export function formatPortfolioLoadSnippet(
  load: Pick<
    PortfolioLoadItem,
    "customer_count" | "member_count" | "open_value" | "attention_count"
  >,
): string {
  return [
    formatCustomerCountShort(load.customer_count),
    formatCompactOpenValue(load.open_value),
    formatAttentionCount(load.attention_count),
    formatMemberCountShort(load.member_count),
  ].join(" · ");
}

/** Linha por pessoa: `5 cli · R$ 1,7 mi · Atenção 4 · 2 carteiras` */
export function formatPersonLoadSnippet(
  load: Pick<
    PersonLoadItem,
    "customer_count" | "portfolio_count" | "open_value" | "attention_count"
  >,
): string {
  return [
    formatCustomerCountShort(load.customer_count),
    formatCompactOpenValue(load.open_value),
    formatAttentionCount(load.attention_count),
    formatPortfolioCountShort(load.portfolio_count),
  ].join(" · ");
}
