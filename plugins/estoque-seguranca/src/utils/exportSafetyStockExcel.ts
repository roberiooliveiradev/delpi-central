import { exportPayloadToXlsx, type TableExportPayload } from "@delpi/plugin-ui/index";

import { fetchSafetyStockItems } from "../api/safetyStockApi";
import type { SafetyStockItem, SafetyStockQueryParams } from "../types/safetyStock";
import { MAX_PAGE_SIZE } from "../types/safetyStock";
import {
  computeDisplayBalance,
  computeDisplayDeficit,
} from "./formatters";
import { safetyStockStatusLabel } from "./safetyStockStatus";

const EXPORT_COLUMNS = [
  { key: "product_code", label: "Código" },
  { key: "product_description", label: "Descrição" },
  { key: "unit", label: "Unidade" },
  { key: "product_group", label: "Grupo" },
  { key: "safety_stock", label: "Est. segurança" },
  { key: "display_balance", label: "Saldo (01+98+99)" },
  { key: "deficit_quantity", label: "Déficit" },
  { key: "status", label: "Situação" },
  { key: "primary_stock", label: "Armazém 01" },
  { key: "warehouse_98_stock", label: "Armazém 98" },
  { key: "warehouse_99_stock", label: "Armazém 99" },
  { key: "blocked", label: "Bloqueado" },
] as const;

export function safetyStockItemToExportRow(
  item: SafetyStockItem,
): Record<string, string | number> {
  return {
    product_code: item.product_code,
    product_description: item.product_description || "",
    unit: item.unit || "",
    product_group: item.product_group || "",
    safety_stock: item.safety_stock,
    display_balance: computeDisplayBalance(item),
    deficit_quantity: computeDisplayDeficit(item),
    status: safetyStockStatusLabel(item.status),
    primary_stock: item.primary_stock,
    warehouse_98_stock: item.warehouse_98_stock,
    warehouse_99_stock: item.warehouse_99_stock,
    blocked: item.blocked ? "Sim" : "Não",
  };
}

export function buildSafetyStockExportPayload(
  items: SafetyStockItem[],
): TableExportPayload {
  return {
    title: "Materias-primas estoque de seguranca",
    columns: [...EXPORT_COLUMNS],
    rows: items.map(safetyStockItemToExportRow),
  };
}

export async function fetchAllSafetyStockItemsForExport(
  params: SafetyStockQueryParams,
  options: { signal?: AbortSignal } = {},
): Promise<SafetyStockItem[]> {
  const pageSize = MAX_PAGE_SIZE;
  let page = 1;
  const items: SafetyStockItem[] = [];

  while (true) {
    const response = await fetchSafetyStockItems(params, page, pageSize, options);
    items.push(...response.items);
    if (items.length >= response.total || response.items.length < pageSize) {
      break;
    }
    page += 1;
  }

  return items;
}

export async function exportSafetyStockExcel(
  params: SafetyStockQueryParams,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const items = await fetchAllSafetyStockItemsForExport(params, options);
  if (!items.length) {
    throw new Error("Não há matérias-primas para exportar com os filtros atuais.");
  }

  const branch = params.branch || "filial";
  exportPayloadToXlsx(buildSafetyStockExportPayload(items), {
    filename: `estoque-seguranca_${branch}`,
  });
}
