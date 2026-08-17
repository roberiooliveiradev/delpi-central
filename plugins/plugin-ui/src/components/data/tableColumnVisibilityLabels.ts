import type { TableColumnVisibilityMenuLabels } from "./TableColumnVisibilityMenu";

/** Textos PT-BR padrão do menu “Colunas” (Pedidos de Vendas / DataTableSection). */
export const DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS: TableColumnVisibilityMenuLabels = {
  trigger: "Colunas",
  panelTitle: "Exibir colunas",
  reset: "Restaurar",
  hint: "Marque para exibir e arraste para reordenar. A preferência é salva neste navegador.",
  columnAriaLabel: (columnLabel: string) => `Exibir coluna ${columnLabel}`,
  panelAriaLabel: "Colunas visíveis",
  reorderAriaLabel: (columnLabel: string) => `Reordenar coluna ${columnLabel}`,
};
