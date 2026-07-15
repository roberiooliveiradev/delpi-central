/**
 * Junta classe BEM do plugin (`{prefix}-…`) com classe estável canônica (`delpi-ui-…`).
 * O CSS canônico estiliza só `.delpi-ui-*` — evita attribute selectors frágeis.
 */
export function delpiUiClass(prefixClass: string, uiClass: string): string {
  return `${prefixClass} ${uiClass}`;
}
