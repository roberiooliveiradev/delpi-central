/**
 * Junta classe BEM do plugin (`{prefix}-…`) com classe estável canônica (`delpi-ui-…`).
 * O CSS canônico estiliza só `.delpi-ui-*` — evita attribute selectors frágeis.
 */
export function delpiUiClass(prefixClass: string, uiClass: string): string {
  return prefixClass === uiClass ? uiClass : `${prefixClass} ${uiClass}`;
}

/** Aplica `--modifier` a cada token (prefix + delpi-ui), preservando as bases. */
export function withBemModifier(classNames: string, modifier: string): string {
  return classNames
    .split(/\s+/)
    .filter(Boolean)
    .flatMap((token) => [token, `${token}--${modifier}`])
    .join(" ");
}
