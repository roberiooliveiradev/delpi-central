/**
 * Natureza financeira dos KPIs (contrato BFF, não toggle inventado).
 * ROL / Minha Carteira líquido = net. Bruto = gross (F2_VALBRUT / gross_revenue).
 * Carteira em aberto = open_order_value (valor aberto de pedido).
 */

export type BillingNature = "net" | "gross" | "open_order_value";

/** Naturezas de faturamento da Minha Carteira (Fat.12m, série, ranking, share). */
export type PortfolioBillingAmountNature = "gross" | "net";

export const PORTFOLIO_BILLING_AMOUNT_NATURES = ["gross", "net"] as const;

/** Default da sessão Minha Carteira — preserva Fat.12m histórico (F2_VALBRUT). */
export const DEFAULT_PORTFOLIO_BILLING_NATURE: PortfolioBillingAmountNature = "gross";

export const BILLING_NATURE_CONTENT = {
  net: {
    id: "net" as const,
    shortLabel: "Líquido",
    hint: "Receita operacional líquida (ROL): vendas SD2 menos impostos e devoluções SD1.",
  },
  open_order_value: {
    id: "open_order_value" as const,
    shortLabel: "Valor aberto",
    hint: "Natureza atual: valor em aberto de pedido (snapshot). Não é ROL líquido nem bruto.",
  },
  gross: {
    id: "gross" as const,
    shortLabel: "Bruto",
    hint: "Faturamento bruto de NF (F2_VALBRUT) na série/Fat.12m; ranking/share usam gross_revenue do envelope ROL.",
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

/**
 * Gross disponível quando o payload declara nature=gross **ou**
 * `supportedNatures` inclui gross (carteira / enrichment / série).
 */
export function isGrossBillingNatureAvailable(
  natureOrSupported: string | readonly string[] | null | undefined,
): boolean {
  if (Array.isArray(natureOrSupported)) {
    return natureOrSupported.includes("gross");
  }
  return natureOrSupported === "gross";
}

/** Toggle Bruto/Líquido só com contrato que declare ambas as naturezas. */
export function isPortfolioBillingNatureToggleAvailable(
  supportedNatures: readonly string[] | null | undefined,
): boolean {
  if (!supportedNatures?.length) return false;
  return (
    supportedNatures.includes("gross") && supportedNatures.includes("net")
  );
}

export function normalizePortfolioBillingNature(
  value: string | null | undefined,
): PortfolioBillingAmountNature {
  const normalized = (value ?? "").trim().toLowerCase();
  return normalized === "net" ? "net" : DEFAULT_PORTFOLIO_BILLING_NATURE;
}

/** Naturezas suportadas pelo contrato atual da carteira (BFF). */
export const PORTFOLIO_SUPPORTED_BILLING_NATURES: readonly PortfolioBillingAmountNature[] =
  PORTFOLIO_BILLING_AMOUNT_NATURES;
