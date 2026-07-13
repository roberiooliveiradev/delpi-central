/**
 * Z-index de portais no `document.body`.
 * Selects/menus ancorados ficam acima do modal (senão o painel abre “atrás”
 * e parece que o Período/select não responde — React overlay nesting).
 * HelpTooltip permanece no topo.
 */
export const DELPI_UI_OVERLAY_Z_INDEX = {
  shapeDialog: 10300,
  modal: 10400,
  /** FormSelect, menus ancorados — acima de `.td-modal` / ModalShell. */
  anchoredPanel: 10500,
  helpTooltip: 11000,
} as const;
