import type { PedidosVendaAbertosItem } from "../types/pedidosVendaAbertos";
import { formatDisplayDate } from "./dates";
import { getLineOpPrevisao } from "./opAllocation";
import { getAllocatedStock } from "./stockAllocation";
import { getLineStatus } from "./statusBadges";
import type { TableColumnDef, TableColumnKey } from "./tableColumns";

type ExportCellValue = string | number | null;

function itemExportValue(item: PedidosVendaAbertosItem, key: TableColumnKey): ExportCellValue {
  const previsao = getLineOpPrevisao(item);

  switch (key) {
    case "nome_cliente":
      return item.nome_cliente || "";
    case "loja_cadastro":
      return item.loja_cadastro || "";
    case "filial":
      return item.filial || "";
    case "pedido":
      return item.linha ? `${item.pedido || ""} / Linha ${item.linha}` : item.pedido || "";
    case "pedido_cliente":
      return item.pedido_cliente || "";
    case "produto":
      return item.produto || "";
    case "codigo_cliente":
      return item.codigo_cliente || "";
    case "quantidade":
      return item.quantidade ?? 0;
    case "entregue":
      return item.entregue ?? 0;
    case "saldo":
      return item.saldo ?? 0;
    case "no_estoque":
      return getAllocatedStock(item);
    case "data_entrega":
      return item.data_entrega ? formatDisplayDate(item.data_entrega) : "";
    case "previsao_entrega_op":
      return previsao.previsaoLabel === "—" ? "" : previsao.previsaoLabel;
    case "data_despacho":
      return item.data_despacho ? formatDisplayDate(item.data_despacho) : "";
    case "valor_aberto":
      return item.valor_aberto ?? 0;
    case "status":
      return getLineStatus(item).label;
    default:
      return "";
  }
}

function buildFilename(): string {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const time = now.toTimeString().slice(0, 5).replace(":", "");
  return `pedidos-venda-abertos_${date}_${time}.xlsx`;
}

export async function exportPedidosExcel(
  items: PedidosVendaAbertosItem[],
  columns: TableColumnDef[],
): Promise<void> {
  if (items.length === 0 || columns.length === 0) {
    return;
  }

  const XLSX = await import("xlsx");
  const headers = columns.map((column) => column.label);
  const rows = items.map((item) =>
    columns.map((column) => itemExportValue(item, column.key)),
  );

  const worksheet = XLSX.utils.aoa_to_sheet([headers, ...rows]);
  worksheet["!cols"] = headers.map((header, columnIndex) => {
    const maxLen = Math.max(
      header.length,
      ...rows.map((row) => String(row[columnIndex] ?? "").length),
    );
    return { wch: Math.min(maxLen + 2, 48) };
  });

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Pedidos em aberto");
  XLSX.writeFile(workbook, buildFilename());
}
