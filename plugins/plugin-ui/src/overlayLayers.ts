/**
 * Z-index de portais no `document.body`.
 * HelpTooltip deve ficar acima de painéis ancorados e modais.
 */
export const DELPI_UI_OVERLAY_Z_INDEX = {
  anchoredPanel: 10200,
  shapeDialog: 10300,
  modal: 10400,
  helpTooltip: 11000,
} as const;
