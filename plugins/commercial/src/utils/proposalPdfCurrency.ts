import type { ProposalDocumentPdfExportOverrides } from "../types/proposalsDocument";

/** Moeda escolhida na emissão do PDF da proposta. */
export type ProposalPdfCurrency = "brl" | "usd";

/**
 * Idioma do PDF derivado da moeda: proposta em dólar sai em inglês.
 * Os rótulos EN são canonizados no renderer da api-delpi (labels do documento);
 * valores não são convertidos — só os títulos/textos fixos mudam.
 */
export function proposalPdfIdioma(
  currency: ProposalPdfCurrency,
): ProposalDocumentPdfExportOverrides["idioma"] {
  return currency === "usd" ? "en" : undefined;
}
