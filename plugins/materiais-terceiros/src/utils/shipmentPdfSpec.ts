import type { Shipment, ShipmentReturn } from "../types/thirdPartyMaterials";
import { branchLabel, formatDatePtBr, formatQuantity, formatStatus } from "./formatters";

export type ShipmentPdfBadgeTone = "approved" | "rejected" | "neutral";

export type ShipmentPdfSummaryLine = {
  label: string;
  value: string;
};

export type ShipmentPdfSpec = {
  documentTitle: string;
  subtitle?: string;
  badge?: string;
  badgeTone?: ShipmentPdfBadgeTone;
  runningMeta?: string;
  summaryLines?: ShipmentPdfSummaryLine[];
  tables?: Array<{
    title: string;
    columns: Array<{ key: string; label: string }>;
    rows: Record<string, unknown>[];
  }>;
  footerNote?: string;
  footerContext?: string;
};

function text(value: string | null | undefined): string {
  const trimmed = String(value ?? "").trim();
  return trimmed || "—";
}

function partnerTypeLabel(value: string | null | undefined): string {
  const token = String(value ?? "").trim().toUpperCase();
  if (token === "C") return "Cliente";
  if (token === "F") return "Fornecedor";
  return text(value);
}

function badgeTone(status: string): ShipmentPdfBadgeTone {
  if (status === "completed") return "approved";
  return "neutral";
}

function returnRows(returns: ShipmentReturn[], unit: string | null) {
  return returns.map((row) => ({
    number: text(row.number),
    series: text(row.series),
    issued: formatDatePtBr(row.issued_on),
    posted: formatDatePtBr(row.posted_on),
    tes: text(row.tes),
    quantity: formatQuantity(row.quantity, unit),
    after: formatQuantity(row.balance_after_return, unit),
    partnerType: partnerTypeLabel(row.partner_type),
  }));
}

export function buildShipmentDelpiDocumentSpec(shipment: Shipment): ShipmentPdfSpec {
  const nf = text(shipment.receipt_invoice.number);
  const product = text(shipment.product.code);
  const partner = text(shipment.partner.name || shipment.partner.code);
  const statusLabel = formatStatus(String(shipment.status));
  const unit = shipment.product.unit;
  const returns = shipment.returns ?? [];

  return {
    documentTitle: "Materiais de Terceiros",
    subtitle: `Remessa ${nf} · ${product} · ${partner}`,
    badge: statusLabel,
    badgeTone: badgeTone(String(shipment.status)),
    runningMeta: `${product} · NF ${nf}`,
    summaryLines: [
      { label: "Filial", value: branchLabel(shipment.branch) },
      { label: "Identidade", value: text(shipment.shipment_id) },
      { label: "Status", value: statusLabel },
      { label: "Produto", value: product },
      { label: "Ref. cliente", value: text(shipment.product.customer_reference) },
      { label: "Descrição", value: text(shipment.product.description) },
      { label: "Unidade", value: text(unit) },
      { label: "Cliente", value: partner },
      { label: "Código / loja", value: `${text(shipment.partner.code)} / ${text(shipment.partner.store)}` },
      { label: "NF recebimento", value: nf },
      { label: "Série", value: text(shipment.receipt_invoice.series) },
      { label: "Emissão", value: formatDatePtBr(shipment.receipt_invoice.issued_on) },
      { label: "Digitação", value: formatDatePtBr(shipment.receipt_invoice.posted_on) },
      { label: "TES entrada", value: text(shipment.receipt_invoice.tes) },
      { label: "Qtd. recebida", value: formatQuantity(shipment.received_quantity, unit) },
      { label: "Qtd. devolvida", value: formatQuantity(shipment.returned_quantity, unit) },
      { label: "Saldo pendente", value: formatQuantity(shipment.pending_balance, unit) },
      { label: "Diferença de controle", value: formatQuantity(shipment.control_difference) },
      { label: "Devoluções", value: returns.length ? String(returns.length) : "Nenhuma" },
    ],
    tables: returns.length
      ? [
          {
            title: "Devoluções",
            columns: [
              { key: "number", label: "NF retorno" },
              { key: "series", label: "Série" },
              { key: "issued", label: "Emissão" },
              { key: "posted", label: "Digitação" },
              { key: "tes", label: "TES" },
              { key: "quantity", label: "Quantidade" },
              { key: "after", label: "Saldo após retorno" },
              { key: "partnerType", label: "Tipo parceiro" },
            ],
            rows: returnRows(returns, unit),
          },
        ]
      : undefined,
    footerNote: "Relatório gerado pelo Minha DELPI.",
    footerContext: `Remessa ${nf} · ${product}`,
  };
}
