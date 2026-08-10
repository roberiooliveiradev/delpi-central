import { formatDisplayDate } from "../../../utils/dates";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import type { CustomerSummary } from "../types/customerSummary";
import { resolveCustomerStatus, statusLabel } from "./customerListPresentation";
import type { CustomerColumnDef, CustomerColumnKey } from "./customerTableColumns";

type ExportCellValue = string | number;
type CustomerTableExportPayload = {
  title: string;
  columns: Array<{ key: string; label: string }>;
  rows: Array<Record<string, unknown>>;
};

function billingTrendLabel(customer: CustomerSummary): string {
  const trend = customer.billingTrend;
  const label =
    trend === "up"
      ? "Alta"
      : trend === "down"
        ? "Queda"
        : trend === "stable"
          ? "Estável"
          : "Dados insuficientes";
  return customer.billingTrendPct == null
    ? label
    : `${label} (${customer.billingTrendPct.toLocaleString("pt-BR", {
        maximumFractionDigits: 1,
      })}%)`;
}

export function customerExportValue(
  customer: CustomerSummary,
  key: CustomerColumnKey,
): ExportCellValue {
  switch (key) {
    case "nome": {
      const codeStore =
        formatEntityCodeStore(customer.codigo, customer.loja) ??
        `${customer.codigo}-${customer.loja}`;
      return customer.nome ? `${customer.nome} (${codeStore})` : codeStore;
    }
    case "sellerName":
      return customer.sellerName?.trim() || "";
    case "city":
      return [customer.city, customer.state].filter(Boolean).join(" / ");
    case "lastPurchaseDate":
      return customer.lastPurchaseDate ? formatDisplayDate(customer.lastPurchaseDate) : "";
    case "billed12m":
      return customer.billed12m ?? 0;
    case "billingTrend":
      return billingTrendLabel(customer);
    case "status":
      return statusLabel(customer.status ?? resolveCustomerStatus(customer));
    case "valorTotalAberto":
      return customer.valorTotalAberto;
    case "quantidadePedidosAtrasados":
      return customer.quantidadePedidosAtrasados;
    case "proximaEntrega":
      return customer.proximaEntrega ? formatDisplayDate(customer.proximaEntrega) : "";
  }
}

export function buildCustomersExportPayload(
  customers: CustomerSummary[],
  columns: CustomerColumnDef[],
): CustomerTableExportPayload {
  return {
    title: "Clientes da carteira",
    columns: columns.map((column) => ({ key: column.key, label: column.label })),
    rows: customers.map((customer) =>
      Object.fromEntries(
        columns.map((column) => [column.key, customerExportValue(customer, column.key)]),
      ),
    ),
  };
}
