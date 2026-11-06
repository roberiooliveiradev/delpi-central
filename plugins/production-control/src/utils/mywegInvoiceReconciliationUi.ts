import type {
  MyWegInvoiceCoverageStatus,
  MyWegInvoiceMatchStatus,
} from "../types";
import { formatDecimalString } from "./formatDecimalString";

/** Exibe quantidade decimal sem converter null em zero. */
export function formatNullableDecimalUn(
  value: string | null | undefined,
  emptyLabel = "Não disponível",
): string {
  if (value == null || String(value).trim() === "") return emptyLabel;
  return `${formatDecimalString(value)} UN`;
}

export function formatNullableDecimal(
  value: string | null | undefined,
  emptyLabel = "Não disponível",
): string {
  if (value == null || String(value).trim() === "") return emptyLabel;
  return formatDecimalString(value);
}

export function isCoverageComplete(status: MyWegInvoiceCoverageStatus | undefined): boolean {
  return (status ?? "").trim() === "complete";
}

export function canShowPostedAsFact(
  coverageStatus: MyWegInvoiceCoverageStatus | undefined,
  postedQuantityUn: string | null | undefined,
): boolean {
  return isCoverageComplete(coverageStatus) && postedQuantityUn != null;
}

export function coverageStatusLabel(status: MyWegInvoiceCoverageStatus | undefined): string {
  switch ((status ?? "").trim()) {
    case "complete":
      return "Cobertura completa";
    case "partial":
      return "Cobertura parcial";
    case "pending_invoice_ingestion":
      return "Aguardando importação fiscal";
    case "conflict":
      return "Divergência entre observações";
    case "unavailable":
      return "Dados fiscais indisponíveis";
    default:
      return status?.trim() ? String(status) : "Cobertura desconhecida";
  }
}

export function completeCoverageDetailLabel(postedQuantityUn: string | null | undefined): string {
  if (postedQuantityUn == null || String(postedQuantityUn).trim() === "") {
    return "Sem NF confirmado";
  }
  const raw = String(postedQuantityUn).trim();
  if (raw === "0" || raw === "0.0" || raw === "0.00") {
    return "Sem NF confirmado";
  }
  return "Com NF";
}

export function invoiceMatchStatusLabel(status: MyWegInvoiceMatchStatus | undefined | null): string {
  switch ((status ?? "").trim()) {
    case "reconciled":
      return "Conciliado";
    case "none":
      return "Sem sinal fiscal";
    case "ambiguous_identity":
      return "Identidade ambígua";
    case "attributed_elsewhere":
      return "NF em outra identidade";
    case "multi_material_key":
      return "Múltiplos materiais";
    case "partial_coverage":
      return "Cobertura parcial";
    case "conflict":
      return "Conflito fiscal";
    case "unavailable":
      return "Fiscal indisponível";
    default:
      return status?.trim() ? String(status) : "—";
  }
}

/** Tom visual só quando o valor existe; null permanece neutro. */
export function nullableDeltaToneClass(value: string | null | undefined): string {
  if (value == null || String(value).trim() === "") return "ppc-myweg-needs__delta";
  const raw = String(value).trim();
  if (raw === "0" || raw === "0.0" || raw === "0.00") return "ppc-myweg-needs__delta";
  if (raw.startsWith("-")) return "ppc-myweg-needs__delta ppc-myweg-needs__delta--down";
  return "ppc-myweg-needs__delta ppc-myweg-needs__delta--up";
}

export function lastCoveredDocumentDate(params: {
  coveredDates?: string[] | null;
  canonicalObservations?: Array<{ documentDate?: string | null; status?: string | null }> | null;
}): string | null {
  const covered = (params.coveredDates ?? []).filter(Boolean);
  if (covered.length > 0) {
    return [...covered].sort().at(-1) ?? null;
  }
  const fromCanonical = (params.canonicalObservations ?? [])
    .filter(
      (row) =>
        row.documentDate &&
        (row.status === "selected" || row.status === "empty_signaled"),
    )
    .map((row) => String(row.documentDate));
  if (fromCanonical.length === 0) return null;
  return [...fromCanonical].sort().at(-1) ?? null;
}

export function isZeroDecimal(value: string | null | undefined): boolean {
  if (value == null) return false;
  const raw = String(value).trim();
  return raw === "0" || raw === "0.0" || raw === "0.00";
}
