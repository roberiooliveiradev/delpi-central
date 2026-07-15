import type { SortKey } from "./sortItems";
import { PVA_COL_COMPACT, PVA_COL_NUMERIC } from "../ui/tableChrome";

export type TableColumnKey =
  | "nome_cliente"
  | "loja_cadastro"
  | "filial"
  | "pedido"
  | "pedido_cliente"
  | "produto"
  | "codigo_cliente"
  | "quantidade"
  | "entregue"
  | "saldo"
  | "no_estoque"
  | "data_entrega"
  | "data_despacho"
  | "valor_aberto"
  | "status"
  | "previsao_entrega_op";

export type TableColumnDef = {
  key: TableColumnKey;
  label: string;
  sortable?: boolean;
  className?: string;
};

export const TABLE_COLUMNS: TableColumnDef[] = [
  { key: "nome_cliente", label: "Cliente", sortable: true },
  { key: "loja_cadastro", label: "Loja", sortable: true, className: PVA_COL_COMPACT },
  { key: "filial", label: "Filial", sortable: true, className: PVA_COL_COMPACT },
  { key: "pedido", label: "Pedido", sortable: true },
  { key: "pedido_cliente", label: "Pedido cliente", sortable: true },
  { key: "produto", label: "Produto", sortable: true },
  { key: "codigo_cliente", label: "Cód. cliente" },
  { key: "quantidade", label: "Qtd.", className: PVA_COL_NUMERIC },
  { key: "entregue", label: "Entregue", className: PVA_COL_NUMERIC },
  { key: "saldo", label: "Saldo", sortable: true, className: PVA_COL_NUMERIC },
  { key: "no_estoque", label: "Est. alocado", className: PVA_COL_NUMERIC },
  { key: "data_entrega", label: "Entrega pedido", sortable: true },
  { key: "previsao_entrega_op", label: "Previsão entrega (OP)", sortable: true },
  { key: "data_despacho", label: "Despacho", sortable: true },
  { key: "valor_aberto", label: "Valor aberto", sortable: true, className: PVA_COL_NUMERIC },
  { key: "status", label: "Status estoque" },
];

export const TABLE_COLUMN_KEYS = TABLE_COLUMNS.map((column) => column.key);

export function isSortableTableColumnKey(key: TableColumnKey): key is SortKey {
  const column = TABLE_COLUMNS.find((item) => item.key === key);
  return Boolean(column?.sortable);
}

export function createDefaultColumnPreferences(): TableColumnPreferences {
  return {
    visibility: Object.fromEntries(
      TABLE_COLUMN_KEYS.map((key) => [key, true]),
    ) as Record<TableColumnKey, boolean>,
  };
}

export type TableColumnPreferences = {
  visibility: Record<TableColumnKey, boolean>;
};
