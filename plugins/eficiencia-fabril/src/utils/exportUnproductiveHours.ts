import type { UnproductiveHoursItem, UnproductiveHoursQueryFilters } from "../types/unproductiveHours";
import { resolveItemCost, resolveItemHours } from "../types/unproductiveHours";
import { formatDisplayDate } from "./dates";
import { formatCurrency, formatHours } from "./format";
import { exportTableExcel, exportTablePdf, type ExportTable } from "./exportDocument";

function cell(value: string | null | undefined): string {
  const trimmed = value?.trim();
  return trimmed ? trimmed : "";
}

function motivoLabel(item: UnproductiveHoursItem): string {
  const code = cell(item.stop_reason ?? item.motivo);
  const description = cell(item.stop_reason_description ?? item.motivoDescricao ?? undefined);
  if (code && description) return `${code} — ${description}`;
  return code || description;
}

function itemToRow(item: UnproductiveHoursItem): (string | number)[] {
  return [
    formatDisplayDate(item.reference_date ?? item.dataReferencia),
    cell(item.production_order ?? item.op),
    cell(item.product_code ?? item.produto),
    cell(item.operation ?? item.operacao),
    cell(item.resource ?? item.recurso),
    cell(item.cost_center ?? item.centroCusto),
    cell(item.operator_name ?? item.nomeOperador),
    motivoLabel(item),
    formatHours(resolveItemHours(item)),
    formatCurrency(resolveItemCost(item)),
    cell(item.observation ?? item.observacao),
  ];
}

const HEADERS = [
  "Data",
  "OP",
  "Produto",
  "Operação",
  "Recurso",
  "Centro de custo",
  "Operador",
  "Motivo",
  "Horas",
  "Valor parada",
  "Observação",
] as const;

function buildExportTable(items: UnproductiveHoursItem[]): ExportTable {
  return {
    title: "Horas improdutivas — apontamentos",
    sheetName: "Horas improdutivas",
    headers: [...HEADERS],
    rows: items.map(itemToRow),
  };
}

function buildFilename(filters: UnproductiveHoursQueryFilters): string {
  const safe = (value: string) => value.replace(/[^\d-]/g, "");
  return `horas-improdutivas_${filters.branch}_${safe(filters.start_date)}_${safe(filters.end_date)}`;
}

export async function exportUnproductiveHoursExcel(
  items: UnproductiveHoursItem[],
  filters: UnproductiveHoursQueryFilters,
): Promise<void> {
  await exportTableExcel(buildExportTable(items), buildFilename(filters));
}

export async function exportUnproductiveHoursPdf(
  items: UnproductiveHoursItem[],
  filters: UnproductiveHoursQueryFilters,
): Promise<void> {
  await exportTablePdf(buildExportTable(items), buildFilename(filters));
}
