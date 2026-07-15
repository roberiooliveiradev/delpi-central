import { exportPayloadToXlsx, type TableExportPayload } from "@delpi/plugin-ui/index";

import { fetchInadimplenciaClientes } from "../api/inadimplenciaApi";
import type {
  ClientesSortBy,
  InadimplenciaClienteItem,
  PeriodFilter,
  SortDirection,
} from "../types/inadimplencia";

const CLIENTES_EXPORT_COLUMNS = [
  { key: "cliente_codigo", label: "Código" },
  { key: "loja", label: "Loja" },
  { key: "nome_cliente", label: "Cliente" },
  { key: "nome_reduzido", label: "Nome reduzido" },
  { key: "total_titulos", label: "Títulos" },
  { key: "titulos_em_dia", label: "Em dia" },
  { key: "titulos_atraso", label: "Atrasados" },
  { key: "percentual_em_dia_qtd", label: "Pontualidade qtd (%)" },
  { key: "percentual_em_dia_valor", label: "Pontualidade valor (%)" },
  { key: "valor_total", label: "Valor total" },
  { key: "valor_atraso", label: "Valor atrasado" },
] as const;

export type ClientesExportFilters = PeriodFilter & {
  search: string;
  sortBy: ClientesSortBy;
  sortDir: SortDirection;
  onlyWithDelays: boolean;
};

export function clienteToExportRow(
  item: InadimplenciaClienteItem,
): Record<string, string | number> {
  return {
    cliente_codigo: item.cliente_codigo,
    loja: item.loja,
    nome_cliente: item.nome_cliente || "",
    nome_reduzido: item.nome_reduzido || "",
    total_titulos: item.total_titulos,
    titulos_em_dia: item.titulos_em_dia,
    titulos_atraso: item.titulos_atraso,
    percentual_em_dia_qtd: Number(item.percentual_em_dia_qtd.toFixed(2)),
    percentual_em_dia_valor: Number(item.percentual_em_dia_valor.toFixed(2)),
    valor_total: item.valor_total,
    valor_atraso: item.valor_atraso,
  };
}

export function buildClientesExportPayload(
  items: InadimplenciaClienteItem[],
): TableExportPayload {
  return {
    title: "Clientes inadimplencia",
    columns: [...CLIENTES_EXPORT_COLUMNS],
    rows: items.map(clienteToExportRow),
  };
}

export async function fetchAllClientesForExport(
  filters: ClientesExportFilters,
): Promise<InadimplenciaClienteItem[]> {
  const pageSize = 100;
  let page = 1;
  const items: InadimplenciaClienteItem[] = [];

  while (true) {
    const response = await fetchInadimplenciaClientes({
      startDate: filters.startDate,
      endDate: filters.endDate,
      page,
      pageSize,
      sortBy: filters.sortBy,
      sortDir: filters.sortDir,
      q: filters.search,
      onlyWithDelays: filters.onlyWithDelays,
    });
    items.push(...response.items);
    if (items.length >= response.total_items || response.items.length < pageSize) {
      break;
    }
    page += 1;
  }

  return items;
}

export async function exportClientesExcel(
  filters: ClientesExportFilters,
): Promise<void> {
  const items = await fetchAllClientesForExport(filters);
  if (!items.length) {
    throw new Error("Não há clientes para exportar com os filtros atuais.");
  }

  const start = filters.startDate ?? "inicio";
  const end = filters.endDate ?? "fim";
  exportPayloadToXlsx(buildClientesExportPayload(items), {
    filename: `inadimplencia-clientes_${start}_${end}`,
  });
}
