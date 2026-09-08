import type { RequestTypeSummary } from "../types/requests";

/**
 * Decide which create surface to open from catalog metadata.
 * Specialized features are registered by code only after presentation_mode says specialized.
 */
export function resolveOpenMode(
  type: RequestTypeSummary,
): "specialized" | "schema_driven" | "generic" {
  const mode = (type.presentation_mode || "").trim().toLowerCase();
  if (mode === "specialized") return "specialized";
  if (mode === "schema_driven") return "schema_driven";
  return "generic";
}

/** Maps specialized type codes to known feature modules. */
export function isInvoiceIssuanceSpecialized(type: RequestTypeSummary): boolean {
  return resolveOpenMode(type) === "specialized" && type.code === "invoice-issuance";
}
