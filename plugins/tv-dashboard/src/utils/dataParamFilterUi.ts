/**
 * Apresentação canônica dos filtros de params (fonte / tela / programação / multi / input).
 *
 * - Opção vazia value "" = «Não definido aqui» em select e placeholder de text
 *   (todas as camadas: source, multi, aggregate) — nunca «(usa a fonte)».
 * - «Valores diferentes» = só status visual na multi (sentinel), nunca a opção de limpar.
 * - Filial consolidada = domínio `all` («Todas as filiais»), não a opção vazia.
 */

export const DIVERGED_FILTER_SELECT_VALUE = "__td_filter_diverged__";

/** Camada do formulário de params. */
export type DataParamFilterLayer = "source" | "aggregate" | "multi";

export type FilterSelectOption = { value: string; label: string };

export type FilterUiLabels = {
  /** Aria/title do botão × (ação). */
  clear: string;
  /** Opção/placeholder value="" — padronizado «Não definido aqui». */
  unset: string;
  diverged: string;
  inherited?: string;
  /** Rótulo do domínio `all` (consolidado), não da opção vazia. */
  allBranches?: string;
};

export function resolveFilterLayer(
  filterLayer: DataParamFilterLayer | undefined,
  /** @deprecated Preferir `filterLayer`; false ⇒ aggregate. */
  hydrateDefaultPreset?: boolean,
): DataParamFilterLayer {
  if (filterLayer) return filterLayer;
  return hydrateDefaultPreset === false ? "aggregate" : "source";
}

/**
 * Rótulo da opção value="" / placeholder de text.
 * Camadas source, multi e aggregate: «Não definido aqui».
 * Herança do slide: rótulo de herança. Nunca «Valores diferentes».
 */
export function resolveFilterClearLabel(
  layer: DataParamFilterLayer,
  labels: FilterUiLabels,
  options: { inherited?: boolean } = {},
): string {
  void layer;
  if (options.inherited) return labels.inherited ?? "Herdado do slide";
  return labels.unset;
}

/**
 * Opção vazia do select de filial: sempre «Não definido aqui» (ou herança).
 * Consolidado permanece como valor de domínio `all` (rótulo allBranches).
 */
export function resolveBranchEmptyLabel(
  layer: DataParamFilterLayer,
  opts: {
    allowConsolidated: boolean;
    inherited?: boolean;
    labels: FilterUiLabels;
  },
): string {
  void opts.allowConsolidated;
  return resolveFilterClearLabel(layer, opts.labels, {
    inherited: opts.inherited,
  });
}

export function resolveFilterSelectValue(stored: string, diverged: boolean): string {
  return diverged ? DIVERGED_FILTER_SELECT_VALUE : stored;
}

/**
 * Opções do select: status divergente (se houver) + Não definido aqui + domínio.
 * Sentinel de divergência não é gravável — só estado visual.
 */
export function buildFilterSelectOptions(
  base: FilterSelectOption[],
  opts: {
    clearLabel: string;
    diverged: boolean;
    divergedLabel: string;
  },
): FilterSelectOption[] {
  const clear: FilterSelectOption = { value: "", label: opts.clearLabel };
  if (!opts.diverged) return [clear, ...base];
  return [
    { value: DIVERGED_FILTER_SELECT_VALUE, label: opts.divergedLabel },
    clear,
    ...base,
  ];
}

/** `null` = ignorar (usuário reescolheu o status divergente). */
export function normalizeFilterSelectChange(value: string): string | null {
  if (value === DIVERGED_FILTER_SELECT_VALUE) return null;
  return value;
}

export function canClearFilterValue(opts: {
  diverged: boolean;
  hasStoredValue: boolean;
  locked?: boolean;
}): boolean {
  if (opts.locked) return false;
  return opts.diverged || opts.hasStoredValue;
}

export function resolveFilterTextPlaceholder(
  opts: {
    diverged: boolean;
    aggregateLayer: boolean;
    inherited: boolean;
    fieldDefault?: string | number | boolean;
  },
  labels: FilterUiLabels,
): string {
  if (opts.diverged) return labels.diverged;
  if (opts.inherited) return labels.inherited ?? "Herdado do slide";
  // source / multi / aggregate: mesmo placeholder padronizado.
  void opts.aggregateLayer;
  if (opts.fieldDefault !== undefined && opts.fieldDefault !== null && opts.fieldDefault !== "") {
    return `Padrão: ${opts.fieldDefault}`;
  }
  return labels.unset;
}
