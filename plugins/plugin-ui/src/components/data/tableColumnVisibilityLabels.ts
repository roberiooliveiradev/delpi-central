import type { TableColumnVisibilityMenuLabels } from "../components/data/TableColumnVisibilityMenu";

/** Textos PT-BR padrão do menu “Colunas” (Pedidos de Vendas / DataTableSection). */
export const DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS: TableColumnVisibilityMenuLabels = {
  trigger: "Colunas",
  panelTitle: "Exibir colunas",
  reset: "Restaurar",
  hint: "Escolha quais colunas exibir. A preferência é salva neste navegador.",
  columnAriaLabel: (columnLabel: string) => `Exibir coluna ${columnLabel}`,
  panelAriaLabel: "Colunas visíveis",
};
