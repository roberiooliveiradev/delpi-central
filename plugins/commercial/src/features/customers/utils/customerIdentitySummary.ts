import { buildCustomerKey } from "./customerIdentity";
import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerEnrichmentItem } from "../../../types/portfolio";

/**
 * Shell de identidade da Conta (sem depender de pedidos em aberto).
 */
export function buildIdentityCustomerSummary(input: {
  codigo: string;
  loja: string;
  nome?: string | null;
  enrichment?: CustomerEnrichmentItem | null;
  sellerName?: string | null;
}): CustomerSummary | null {
  const key = buildCustomerKey(input.codigo, input.loja);
  if (!key) return null;
  const codigo = input.codigo.trim();
  const loja = input.loja.trim();
  const enrich = input.enrichment;
  const nome =
    (input.nome || "").trim() ||
    `${codigo}/${loja}`;

  return {
    key,
    codigo,
    loja,
    nome,
    quantidadePedidosAbertos: 0,
    quantidadeLinhasAbertas: 0,
    valorTotalAberto: 0,
    quantidadePedidosAtrasados: 0,
    maiorAtrasoDias: 0,
    proximaEntrega: null,
    quantidadePedidosParciais: 0,
    temAtraso: false,
    temPedidoParcial: false,
    lines: [],
    city: enrich?.city ?? null,
    state: enrich?.state ?? null,
    lastPurchaseDate: enrich?.last_purchase_date ?? null,
    billed12m: enrich?.billed_12m ?? null,
    hasAvatar: enrich?.has_avatar ?? false,
    billingTrend: enrich?.billing_trend ?? null,
    billingTrendPct: enrich?.billing_trend_pct ?? null,
    coverageKnown: Boolean(enrich),
    enrichmentAvailable: Boolean(enrich),
    sellerName: input.sellerName ?? null,
  };
}

/** Prefer orders aggregation; fill gaps from identity shell. */
export function mergeCustomerIdentity(
  fromOrders: CustomerSummary | null | undefined,
  identity: CustomerSummary | null,
): CustomerSummary | null {
  if (fromOrders) {
    if (!identity) return fromOrders;
    return {
      ...fromOrders,
      nome: fromOrders.nome?.trim() || identity.nome,
      city: fromOrders.city ?? identity.city,
      state: fromOrders.state ?? identity.state,
      lastPurchaseDate: fromOrders.lastPurchaseDate ?? identity.lastPurchaseDate,
      billed12m: fromOrders.billed12m ?? identity.billed12m,
      hasAvatar: fromOrders.hasAvatar ?? identity.hasAvatar,
      billingTrend: fromOrders.billingTrend ?? identity.billingTrend,
      billingTrendPct: fromOrders.billingTrendPct ?? identity.billingTrendPct,
      coverageKnown: fromOrders.coverageKnown || identity.coverageKnown,
      enrichmentAvailable:
        fromOrders.enrichmentAvailable || identity.enrichmentAvailable,
      sellerName: fromOrders.sellerName ?? identity.sellerName,
    };
  }
  return identity;
}
