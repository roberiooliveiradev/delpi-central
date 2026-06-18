import type {
  InspecoesEntradaHistoricoDetalhe,
  InspecoesEntradaHistoricoDetalheTest,
} from "../types/inspecoesEntradaHistoricoDetalhe";
import { formatDatePt, formatNumber, formatText } from "./format";
import {
  isFailedTest,
  isNumericTest,
  isTextualTest,
  resolveNumericMeasuredValue,
  resolveTextMeasuredValue,
  resolveTextSpecification,
} from "./testMeasurementDisplay";

const BRANCH_UNIT_LABELS: Record<string, string> = {
  "01": "Jaraguá do Sul/SC",
  "02": "Rio Bananal/ES",
};

export function escapeCertificateHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function formatCertificateMultiline(value: string): string {
  if (!value.trim() || value === "—") return "";
  return escapeCertificateHtml(value).replace(/\n/g, "<br>");
}

export function formatBranchUnitLabel(branch: string): string {
  const normalized = branch.trim();
  if (BRANCH_UNIT_LABELS[normalized]) {
    return BRANCH_UNIT_LABELS[normalized];
  }
  return normalized ? `Filial ${normalized}` : "—";
}

export function formatCertificateSpecification(test: InspecoesEntradaHistoricoDetalheTest): string {
  if (isNumericTest(test)) {
    const lines: string[] = [];

    if (test.nominal_value?.trim()) {
      lines.push(`Nominal: ${test.nominal_value.trim()}`);
    }
    if (test.lower_spec_limit?.trim()) {
      lines.push(`Mín: ${test.lower_spec_limit.trim()}`);
    }
    if (test.upper_spec_limit?.trim()) {
      lines.push(`Máx: ${test.upper_spec_limit.trim()}`);
    }

    if (lines.length > 0) {
      return lines.join("\n");
    }
  }

  if (isTextualTest(test)) {
    const textSpec = resolveTextSpecification(test);
    if (textSpec) return textSpec;
  }

  const expected = test.expected_specification?.trim();
  return expected ? expected : "";
}

export function formatCertificateMeasuredValue(test: InspecoesEntradaHistoricoDetalheTest): string {
  const numeric = resolveNumericMeasuredValue(test);
  if (numeric) return numeric;

  const textual = resolveTextMeasuredValue(test);
  if (textual) return textual;

  return "";
}

export function formatCertificateMeasurementAt(test: InspecoesEntradaHistoricoDetalheTest): string {
  const datePart = test.measurement_date?.trim();
  const timePart = test.measurement_time?.trim();

  if (datePart && timePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? timePart : `${dateLabel} ${timePart}`;
  }

  if (datePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? "" : dateLabel;
  }

  return timePart ?? "";
}

export function collectCertificateInspectorNames(detail: InspecoesEntradaHistoricoDetalhe): string[] {
  const names = new Set<string>();
  const summaryInspector = detail.summary.inspector_name?.trim();

  if (summaryInspector) {
    names.add(summaryInspector);
  }

  for (const test of detail.tests) {
    const inspectorName = test.inspector_name?.trim();
    if (inspectorName) {
      names.add(inspectorName);
    }
  }

  return [...names];
}

export function formatCertificateIssuedAt(date: Date = new Date()): string {
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatCertificateQuantity(summary: InspecoesEntradaHistoricoDetalhe["summary"]): string {
  return `${formatNumber(summary.quantity)} ${formatText(summary.unit)}`;
}

export function formatCertificateReceivedAt(summary: InspecoesEntradaHistoricoDetalhe["summary"]): string | null {
  const datePart = summary.received_date?.trim();
  const timePart = summary.received_time?.trim();
  if (!datePart && !timePart) return null;

  if (datePart && timePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? timePart : `${dateLabel} ${timePart}`;
  }

  if (datePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? null : dateLabel;
  }

  return timePart ?? null;
}

export function formatCertificateReportAt(summary: InspecoesEntradaHistoricoDetalhe["summary"]): string | null {
  const datePart = summary.report_date?.trim();
  const timePart = summary.report_time?.trim();
  if (!datePart && !timePart) return null;

  if (datePart && timePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? timePart : `${dateLabel} ${timePart}`;
  }

  if (datePart) {
    const dateLabel = formatDatePt(datePart);
    return dateLabel === "—" ? null : dateLabel;
  }

  return timePart ?? null;
}

export function formatCertificateProductLabel(summary: InspecoesEntradaHistoricoDetalhe["summary"]): string {
  const code = summary.product_code?.trim();
  const description = summary.product_description?.trim();

  if (code && description) {
    return `${code} — ${description}`;
  }

  return code ? code : "—";
}

export function isCertificateFailedTest(test: InspecoesEntradaHistoricoDetalheTest): boolean {
  return isFailedTest(test);
}

export function resolveCertificateSealClass(result: string): string {
  const normalized = result.trim().toUpperCase();
  if (normalized.includes("REJEIT") || normalized.includes("REPROV")) {
    return "cert-seal--rejected";
  }
  if (normalized.includes("APROV")) {
    return "cert-seal--approved";
  }
  return "cert-seal--neutral";
}
