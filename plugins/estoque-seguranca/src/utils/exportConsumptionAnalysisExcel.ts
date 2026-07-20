import { exportPayloadToXlsx, type TableExportPayload } from "@delpi/plugin-ui/index";

import { fetchConsumptionAnalysisItems } from "../api/safetyStockApi";
import type {
  ConsumptionAnalysisItem,
  ConsumptionAnalysisQueryParams,
} from "../types/consumptionAnalysis";
import { MAX_PAGE_SIZE } from "../types/safetyStock";
import { analysisStatusLabel } from "./safetyStockStatus";

const EXPORT_COLUMNS = [
  { key: "product_code", label: "Código" },
  { key: "product_description", label: "Descrição" },
  { key: "unit", label: "UM" },
  { key: "product_group", label: "Grupo" },
  { key: "safety_stock", label: "ESTSEG atual" },
  { key: "suggested_safety_stock", label: "Sugerido" },
  { key: "difference_quantity", label: "Diferença" },
  { key: "average_daily_consumption", label: "Consumo diário" },
  { key: "period_consumption", label: "Consumo do período" },
  { key: "lead_time_days", label: "Lead time (dias corridos)" },
  { key: "lead_time_business_days", label: "Lead time (dias úteis)" },
  { key: "coverage_business_days", label: "Cobertura (dias úteis)" },
  { key: "available_stock", label: "Saldo disponível" },
  { key: "analysis_status", label: "Situação" },
  { key: "movement_count", label: "Movimentos" },
  { key: "blocked", label: "Bloqueado" },
] as const;

export function consumptionAnalysisItemToExportRow(
  item: ConsumptionAnalysisItem,
): Record<string, string | number> {
  return {
    product_code: item.product_code,
    product_description: item.product_description || "",
    unit: item.unit || "",
    product_group: item.product_group || "",
    safety_stock: item.safety_stock,
    suggested_safety_stock: item.suggested_safety_stock,
    difference_quantity: item.difference_quantity,
    average_daily_consumption: item.average_daily_consumption,
    period_consumption: item.period_consumption,
    lead_time_days: item.lead_time_days,
    lead_time_business_days: item.lead_time_business_days,
    coverage_business_days:
      item.coverage_business_days == null ? "" : item.coverage_business_days,
    available_stock: item.available_stock,
    analysis_status: analysisStatusLabel(item.analysis_status),
    movement_count: item.movement_count,
    blocked: item.blocked ? "Sim" : "Não",
  };
}

export function buildConsumptionAnalysisExportPayload(
  items: ConsumptionAnalysisItem[],
): TableExportPayload {
  return {
    title: "Simulacao estoque de seguranca",
    columns: [...EXPORT_COLUMNS],
    rows: items.map(consumptionAnalysisItemToExportRow),
  };
}

export async function fetchAllConsumptionAnalysisItemsForExport(
  params: ConsumptionAnalysisQueryParams,
  options: { signal?: AbortSignal } = {},
): Promise<ConsumptionAnalysisItem[]> {
  const pageSize = MAX_PAGE_SIZE;
  let page = 1;
  const items: ConsumptionAnalysisItem[] = [];

  while (true) {
    const response = await fetchConsumptionAnalysisItems(
      params,
      page,
      pageSize,
      options,
    );
    items.push(...response.items);
    if (items.length >= response.total || response.items.length < pageSize) {
      break;
    }
    page += 1;
  }

  return items;
}

export async function exportConsumptionAnalysisExcel(
  params: ConsumptionAnalysisQueryParams,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const items = await fetchAllConsumptionAnalysisItemsForExport(params, options);
  if (!items.length) {
    throw new Error("Não há itens da simulação para exportar com os filtros atuais.");
  }

  const branch = params.branch || "filial";
  exportPayloadToXlsx(buildConsumptionAnalysisExportPayload(items), {
    filename: `estoque-seguranca-analise_${branch}`,
  });
}
