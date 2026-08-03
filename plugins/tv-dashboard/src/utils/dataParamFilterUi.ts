/**
 * Apresentação canônica dos filtros de params (fonte / tela / programação / multi).
 *
 * - «Limpar» / «Não definido» = ação value "" (sempre disponível).
 * - «Valores diferentes» = estado de exibição na multi (sentinel), nunca a opção de limpar.
 * Assim, com divergência o usuário ainda consegue escolher Limpar e unificar as fontes.
 */

export const DIVERGED_FILTER_SELECT_VALUE = "__td_filter_diverged__";

/** Camada do formulário de params. */
export type DataParamFilterLayer = "source" | "aggregate" | "multi";

export type FilterSelectOption = { value: string; label: string };

export type FilterUiLabels = {
  clear: string;
  unset: string;
  diverged: string;
  inherited?: string;
};

export function resolveFilterLayer(
  filterLayer: DataParamFilterLayer | undefined,
  /** @deprecated Preferir `filterLayer`; false ⇒ aggregate. */
  hydrateDefaultPreset?: boolean,
): DataParamFilterLayer {
  if (filterLayer) return filterLayer;
  return hydrateDefaultPreset === false ? "aggregate" : "source";
}

/** Rótulo da opção value="" — limpar ou «não definido» na camada agregada. Nunca «Valores diferentes». */
export function resolveFilterClearLabel(
  layer: DataParamFilterLayer,
  labels: FilterUiLabels,
  options: { inherited?: boolean } = {},
): string {
  if (layer === "aggregate") return labels.unset;
  if (options.inherited) return labels.inherited ?? "Herdado do slide";
  return labels.clear;
}

export function resolveFilterSelectValue(stored: string, diverged: boolean): string {
  return diverged ? DIVERGED_FILTER_SELECT_VALUE : stored;
}

/**
 * Opções do select: status divergente (se houver) + Limpar/Não definido + domínio.
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
  if (opts.aggregateLayer) return labels.unset;
  if (opts.inherited) return labels.inherited ?? "Herdado do slide";
  if (opts.fieldDefault !== undefined) return `Padrão: ${opts.fieldDefault}`;
  return labels.clear;
}
