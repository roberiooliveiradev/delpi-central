import { exportPayloadToXlsx, type TableExportPayload } from "@delpi/plugin-ui/index";

import { fetchInadimplenciaTitulos } from "../api/inadimplenciaApi";
import type {
  InadimplenciaTituloItem,
  PeriodFilter,
  SortDirection,
  TituloStatus,
  TitulosSortBy,
} from "../types/inadimplencia";

const TITULOS_EXPORT_COLUMNS = [
  { key: "filial", label: "Filial" },
  { key: "prefixo", label: "Prefixo" },
  { key: "numero", label: "Número" },
  { key: "parcela", label: "Parcela" },
  { key: "tipo", label: "Tipo" },
  { key: "cliente_codigo", label: "Código cliente" },
  { key: "loja", label: "Loja" },
  { key: "nome_cliente", label: "Cliente" },
  { key: "data_emissao", label: "Emissão" },
  { key: "data_vencimento_real", label: "Vencimento real" },
  { key: "data_baixa", label: "Baixa" },
  { key: "valor_titulo", label: "Valor" },
  { key: "pago_em_dia", label: "Pago em dia" },
  { key: "dias_atraso", label: "Dias de atraso" },
  { key: "faixa_atraso", label: "Faixa" },
] as const;

export type TitulosExportFilters = PeriodFilter & {
  customerCode: string;
  storeCode: string;
  search: string;
  sortBy: TitulosSortBy;
  sortDir: SortDirection;
  status: TituloStatus;
  delayRange: string;
};

export function tituloToExportRow(
  item: InadimplenciaTituloItem,
): Record<string, string | number> {
  return {
    filial: item.filial || "",
    prefixo: item.prefixo || "",
    numero: item.numero || "",
    parcela: item.parcela || "",
    tipo: item.tipo || "",
    cliente_codigo: item.cliente_codigo,
    loja: item.loja,
    nome_cliente: item.nome_cliente || item.nome_reduzido || "",
    data_emissao: item.data_emissao || "",
    data_vencimento_real: item.data_vencimento_real || "",
    data_baixa: item.data_baixa || "",
    valor_titulo: item.valor_titulo,
    pago_em_dia: item.pago_em_dia ? "Sim" : "Não",
    dias_atraso: item.dias_atraso,
    faixa_atraso: item.faixa_atraso?.rotulo || item.faixa_atraso?.codigo || "",
  };
}

export function buildTitulosExportPayload(
  items: InadimplenciaTituloItem[],
): TableExportPayload {
  return {
    title: "Titulos cliente",
    columns: [...TITULOS_EXPORT_COLUMNS],
    rows: items.map(tituloToExportRow),
  };
}

export async function fetchAllTitulosForExport(
  filters: TitulosExportFilters,
): Promise<InadimplenciaTituloItem[]> {
  const pageSize = 100;
  let page = 1;
  const items: InadimplenciaTituloItem[] = [];

  while (true) {
    const response = await fetchInadimplenciaTitulos({
      startDate: filters.startDate,
      endDate: filters.endDate,
      customerCode: filters.customerCode,
      storeCode: filters.storeCode,
      status: filters.status,
      delayRange: filters.delayRange || undefined,
      q: filters.search,
      page,
      pageSize,
      sortBy: filters.sortBy,
      sortDir: filters.sortDir,
    });
    items.push(...response.items);
    if (items.length >= response.total_items || response.items.length < pageSize) {
      break;
    }
    page += 1;
  }

  return items;
}

export async function exportTitulosExcel(filters: TitulosExportFilters): Promise<void> {
  const items = await fetchAllTitulosForExport(filters);
  if (!items.length) {
    throw new Error("Não há títulos para exportar com os filtros atuais.");
  }

  const start = filters.startDate ?? "inicio";
  const end = filters.endDate ?? "fim";
  const customer = `${filters.customerCode}-${filters.storeCode}`;
  exportPayloadToXlsx(buildTitulosExportPayload(items), {
    filename: `inadimplencia-titulos_${customer}_${start}_${end}`,
  });
}
