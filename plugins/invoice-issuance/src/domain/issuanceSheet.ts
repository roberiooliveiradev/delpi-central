import { branchLabel } from "../constants/branch";
import { II_SHEET } from "../content/helpTooltips";
import {
  freightModeLabel,
  invoiceTypeLabel,
  partyTypeLabel,
  statusLabel,
} from "./status";
import type { IssuanceItem, IssuanceRequest } from "./types";

export type IssuanceSheetField = {
  label: string;
  value: string;
  hint?: string;
  wide?: boolean;
  copyable?: boolean;
  copyValue?: string;
  format?: "taxId" | "quantity";
};

export type IssuanceSheetSection = {
  id: string;
  title: string;
  fields: IssuanceSheetField[];
};

export function uniqueSalesOrders(items: IssuanceItem[]): string {
  const orders = [
    ...new Set(
      items
        .map((item) => (item.sales_order || "").trim())
        .filter(Boolean),
    ),
  ];
  return orders.join(", ");
}

export function buildIssuanceSheet(request: IssuanceRequest): IssuanceSheetSection[] {
  const salesOrders = uniqueSalesOrders(request.items);
  const invoiceType =
    request.invoice_type === "other" && request.invoice_type_other
      ? `${invoiceTypeLabel(request.invoice_type)} — ${request.invoice_type_other}`
      : invoiceTypeLabel(request.invoice_type);
  const carrier =
    request.carrier_code || request.carrier_name
      ? [request.carrier_code, request.carrier_name].filter(Boolean).join(" — ")
      : "";

  return [
    {
      id: "party",
      title: II_SHEET.party,
      fields: [
        { label: "Tipo", value: partyTypeLabel(request.party_type) },
        {
          label: "Código",
          value: request.party_code,
          hint: II_SHEET.hints.partyCode,
          copyable: true,
        },
        {
          label: "Loja",
          value: request.party_store,
          hint: II_SHEET.hints.partyStore,
          copyable: true,
        },
        { label: "Nome", value: request.party_name, wide: true },
        {
          label: "CNPJ / CPF",
          value: request.tax_id || "",
          hint: II_SHEET.hints.taxId,
          copyable: Boolean(request.tax_id),
          format: "taxId",
        },
      ],
    },
    {
      id: "invoice",
      title: II_SHEET.invoice,
      fields: [
        { label: "Filial", value: branchLabel(request.branch_code) },
        {
          label: "Tipo de NF",
          value: invoiceType,
          hint: II_SHEET.hints.invoiceType,
        },
        {
          label: "Pedido de venda",
          value: salesOrders,
          hint: II_SHEET.hints.salesOrder,
          copyable: Boolean(salesOrders),
        },
      ],
    },
    {
      id: "freight",
      title: II_SHEET.freight,
      fields: [
        {
          label: "Frete",
          value: freightModeLabel(request.freight_mode),
          hint: II_SHEET.hints.freightMode,
        },
        {
          label: "Transportadora",
          value: carrier,
          hint: II_SHEET.hints.carrier,
          copyable: Boolean(request.carrier_code),
          copyValue: request.carrier_code || undefined,
        },
        {
          label: "Peso (kg)",
          value: String(request.weight_kg ?? ""),
          hint: II_SHEET.hints.weight,
          format: "quantity",
        },
        {
          label: "Volumes",
          value: String(request.volume_count ?? ""),
          hint: II_SHEET.hints.volumes,
        },
      ],
    },
    ...(request.observation
      ? [
          {
            id: "extras",
            title: II_SHEET.extras,
            fields: [
              {
                label: "Observação",
                value: request.observation,
                wide: true,
              },
            ],
          },
        ]
      : []),
    {
      id: "situation",
      title: II_SHEET.situation,
      fields: [
        { label: "Status", value: statusLabel(request.status) },
        { label: "Solicitante", value: request.created_by_name },
        { label: "Responsável", value: request.assignee_name || "" },
      ],
    },
  ];
}
