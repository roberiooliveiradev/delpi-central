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

/**
 * Espelha `{prefix}-table__col--*` → `delpi-ui-table__col--*` em colunas do DataTable.
 * MFEs tipicamente passam só o BEM local (`pa-table__col--numeric`); o CSS do kit
 * estiliza só `.delpi-ui-table__col-*`.
 */
export function resolveDataTableColumnClassName(
  className: string | undefined,
): string | undefined {
  const raw = (className ?? "").trim();
  if (!raw) return undefined;

  const tokens = raw.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  const seen = new Set<string>();

  const push = (token: string) => {
    if (seen.has(token)) return;
    seen.add(token);
    out.push(token);
  };

  for (const token of tokens) {
    push(token);
    const match = token.match(/^[a-z0-9][\w-]*-table__col--([a-z0-9-]+)$/i);
    if (match) {
      push(`delpi-ui-table__col--${match[1]}`);
    }
  }

  return out.join(" ");
}
