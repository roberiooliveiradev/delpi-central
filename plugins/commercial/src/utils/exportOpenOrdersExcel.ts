import type { OpenOrdersTotvsItem } from "../types/openOrdersTotvs";
import { exportTableFormat, formatOperationalUnitCode, type TableExportPayload } from "@delpi/plugin-ui/index";
import { formatDisplayDate, getDeliveryOverdueDays } from "./dates";
import {
  DEFAULT_QUANTITY_DISPLAY_MODE,
  type QuantityDisplayMode,
  resolveDisplayQuantity,
} from "./displayQuantity";
import { getLineOpForecast } from "./opAllocation";
import { getAllocatedStock } from "./stockAllocation";
import { getLineStatus } from "./statusBadges";
import type { TableColumnDef, TableColumnKey } from "./tableColumns";

type ExportCellValue = string | number | null;

function displayQty(
  quantity: number | null | undefined,
  unit: string | null | undefined,
  mode: QuantityDisplayMode,
): number {
  return resolveDisplayQuantity(quantity, unit, mode).value;
}

function itemExportValue(
  item: OpenOrdersTotvsItem,
  key: TableColumnKey,
  mode: QuantityDisplayMode,
): ExportCellValue {
  const previsao = getLineOpForecast(item);
  const unit = item.unidade;

  switch (key) {
    case "nome_cliente":
      return item.nome_cliente || "";
    case "loja_cadastro":
      return item.loja_cadastro || "";
    case "filial":
      return formatOperationalUnitCode(item.filial, "");
    case "pedido":
      return item.linha ? `${item.pedido || ""} / Linha ${item.linha}` : item.pedido || "";
    case "pedido_cliente":
      return item.pedido_cliente || "";
    case "produto":
      return item.produto || "";
    case "codigo_cliente":
      return item.codigo_cliente || "";
    case "quantidade":
      return displayQty(item.quantidade, unit, mode);
    case "entregue":
      return displayQty(item.entregue, unit, mode);
    case "saldo":
      return displayQty(item.saldo, unit, mode);
    case "no_estoque":
      return displayQty(getAllocatedStock(item), unit, mode);
    case "cobertura": {
      const allocated = getAllocatedStock(item);
      const saldo = item.saldo ?? 0;
      if (saldo <= 0) return "100%";
      return `${Math.round((allocated / saldo) * 100)}%`;
    }
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
    case "atraso_dias":
      return getDeliveryOverdueDays(item.data_entrega) ?? "";
    default:
      return "";
  }
}

function buildFilename(): string {
  const now = new Date();
  const date = now.toISOString().slice(0, 10);
  const time = now.toTimeString().slice(0, 5).replace(":", "");
  return `pedidos-venda-abertos_${date}_${time}`;
}

function buildPayload(
  items: OpenOrdersTotvsItem[],
  columns: TableColumnDef[],
  mode: QuantityDisplayMode,
): TableExportPayload {
  return {
    title: "Pedidos em aberto",
    columns: columns.map((column) => ({ key: column.key, label: column.label })),
    rows: items.map((item) => {
      const record: Record<string, unknown> = {};
      for (const column of columns) {
        record[column.key] = itemExportValue(item, column.key, mode);
      }
      return record;
    }),
  };
}

export async function exportOpenOrdersExcel(
  items: OpenOrdersTotvsItem[],
  columns: TableColumnDef[],
  mode: QuantityDisplayMode = DEFAULT_QUANTITY_DISPLAY_MODE,
): Promise<void> {
  if (items.length === 0 || columns.length === 0) {
    return;
  }

  exportTableFormat(buildPayload(items, columns, mode), "xlsx", {
    filename: buildFilename(),
  });
}
