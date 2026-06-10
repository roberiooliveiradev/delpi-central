import type { SortKey } from "./sortItems";

export type TableColumnKey =
  | "nome_cliente"
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
  { key: "filial", label: "Filial", sortable: true, className: "pva-table__col--compact" },
  { key: "pedido", label: "Pedido", sortable: true },
  { key: "pedido_cliente", label: "Pedido cliente", sortable: true },
  { key: "produto", label: "Produto", sortable: true },
  { key: "codigo_cliente", label: "Cód. cliente" },
  { key: "quantidade", label: "Qtd.", className: "pva-table__col--numeric" },
  { key: "entregue", label: "Entregue", className: "pva-table__col--numeric" },
  { key: "saldo", label: "Saldo", sortable: true, className: "pva-table__col--numeric" },
  { key: "no_estoque", label: "Est. alocado", className: "pva-table__col--numeric" },
  { key: "data_entrega", label: "Entrega pedido", sortable: true },
  { key: "previsao_entrega_op", label: "Previsão entrega (OP)", sortable: true },
  { key: "data_despacho", label: "Despacho", sortable: true },
  { key: "valor_aberto", label: "Valor aberto", sortable: true, className: "pva-table__col--numeric" },
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
