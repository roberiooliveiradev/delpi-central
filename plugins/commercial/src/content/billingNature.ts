/**
 * Natureza financeira dos KPIs do Overview (contrato BFF, não toggle inventado).
 * ROL = net (líquido). Carteira = open_order_value (valor aberto de pedido).
 * Gross só quando o BFF expuser `nature=gross` — hoje indisponível.
 */

export type BillingNature = "net" | "gross" | "open_order_value";

export const BILLING_NATURE_CONTENT = {
  net: {
    id: "net" as const,
    shortLabel: "Líquido",
    hint: "Natureza atual: receita operacional líquida (ROL). Série bruta indisponível neste contrato.",
  },
  open_order_value: {
    id: "open_order_value" as const,
    shortLabel: "Valor aberto",
    hint: "Natureza atual: valor em aberto de pedido (snapshot). Não é ROL líquido nem bruto.",
  },
  gross: {
    id: "gross" as const,
    shortLabel: "Bruto",
    hint: "Série bruta só quando o BFF entregar nature=gross. Toggle bloqueado sem contrato.",
  },
} as const;

export function billingNatureShortLabel(nature: BillingNature): string {
  return BILLING_NATURE_CONTENT[nature].shortLabel;
}

export function billingNatureHint(nature: BillingNature): string {
  return BILLING_NATURE_CONTENT[nature].hint;
}

export function appendBillingNatureContext(
  context: string,
  nature: BillingNature,
): string {
  const suffix = billingNatureShortLabel(nature);
  if (!context.trim()) return suffix;
  if (context.includes(suffix)) return context;
  return `${context} · ${suffix}`;
}

/** Gross toggle: só habilitado se o payload declarar nature=gross. */
export function isGrossBillingNatureAvailable(nature: string | null | undefined): boolean {
  return nature === "gross";
}
