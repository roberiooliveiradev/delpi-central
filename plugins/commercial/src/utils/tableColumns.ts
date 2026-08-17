import { OPERATIONAL_UNIT_COLUMN_LABEL } from "@delpi/plugin-ui/index";

import type { SortKey } from "./sortItems";

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
  | "cobertura"
  | "data_entrega"
  | "data_despacho"
  | "valor_aberto"
  | "status"
  | "previsao_entrega_op"
  | "atraso_dias";

export type TableColumnDef = {
  key: TableColumnKey;
  label: string;
  sortable?: boolean;
  className?: string;
};

/** Colunas default enxutas (WF-02R-T). */
export const DEFAULT_VISIBLE_COLUMN_KEYS: readonly TableColumnKey[] = [
  "nome_cliente",
  "pedido",
  "produto",
  "cobertura",
  "data_entrega",
  "previsao_entrega_op",
  "status",
  "valor_aberto",
  "atraso_dias",
] as const;

export const TABLE_COLUMNS: TableColumnDef[] = [
  { key: "nome_cliente", label: "Cliente", sortable: true },
  { key: "loja_cadastro", label: "Loja", sortable: true },
  { key: "filial", label: OPERATIONAL_UNIT_COLUMN_LABEL, sortable: true },
  { key: "pedido", label: "Pedido", sortable: true },
  { key: "pedido_cliente", label: "Pedido cliente", sortable: true },
  { key: "produto", label: "Produto", sortable: true },
  { key: "codigo_cliente", label: "Cód. cliente" },
  { key: "quantidade", label: "Qtd." },
  { key: "entregue", label: "Entregue" },
  { key: "saldo", label: "Saldo", sortable: true },
  { key: "no_estoque", label: "Est. alocado" },
  { key: "cobertura", label: "Cobertura", sortable: true },
  { key: "data_entrega", label: "Data de faturamento", sortable: true },
  { key: "previsao_entrega_op", label: "Previsão entrega (OP)", sortable: true },
  { key: "data_despacho", label: "Despacho", sortable: true },
  { key: "valor_aberto", label: "Valor aberto", sortable: true },
  { key: "status", label: "Status estoque", sortable: true },
  { key: "atraso_dias", label: "Atraso (dias)", sortable: true },
];

export const TABLE_COLUMN_KEYS = TABLE_COLUMNS.map((column) => column.key);

export function isSortableTableColumnKey(key: TableColumnKey): key is SortKey {
  const column = TABLE_COLUMNS.find((item) => item.key === key);
  return Boolean(column?.sortable);
}

export function createDefaultColumnVisibility(): Record<TableColumnKey, boolean> {
  const defaults = new Set<string>(DEFAULT_VISIBLE_COLUMN_KEYS);
  return Object.fromEntries(
    TABLE_COLUMN_KEYS.map((key) => [key, defaults.has(key)]),
  ) as Record<TableColumnKey, boolean>;
}

export function createDefaultColumnPreferences(): TableColumnPreferences {
  return {
    visibility: createDefaultColumnVisibility(),
    order: [...TABLE_COLUMN_KEYS],
  };
}

export type TableColumnPreferences = {
  visibility: Record<TableColumnKey, boolean>;
  order: TableColumnKey[];
};
