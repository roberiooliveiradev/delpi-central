/**
 * Junta classe BEM do plugin (`{prefix}-…`) com classe estável canônica (`delpi-ui-…`).
 * O CSS canônico estiliza só `.delpi-ui-*` — evita attribute selectors frágeis.
 */
export function delpiUiClass(prefixClass: string, uiClass: string): string {
  return prefixClass === uiClass ? uiClass : `${prefixClass} ${uiClass}`;
}

/**
 * Garante que a classe canônica exista mesmo quando o MFE passa só o prefixo
 * (`ef-export-actions` → `ef-export-actions delpi-ui-export-actions`).
 */
export function ensureDelpiUiClass(
  className: string | undefined,
  canonical: string,
): string {
  const raw = (className ?? "").trim();
  if (!raw) return canonical;
  const tokens = raw.split(/\s+/).filter(Boolean);
  if (tokens.includes(canonical)) return raw;
  return `${raw} ${canonical}`;
}

/** Aplica `--modifier` a cada token (prefix + delpi-ui), preservando as bases. */
export function withBemModifier(classNames: string, modifier: string): string {
  return classNames
    .split(/\s+/)
    .filter(Boolean)
    .flatMap((token) => [token, `${token}--${modifier}`])
    .join(" ");
}
