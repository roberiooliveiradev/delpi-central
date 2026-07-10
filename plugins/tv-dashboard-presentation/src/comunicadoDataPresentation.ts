import type {
  ComunicadoDataBlockType,
  ComunicadoDataDisplayMode,
} from "./comunicadoTypes";

export type DataPresentationOption = {
  displayMode: ComunicadoDataDisplayMode;
  blockType: ComunicadoDataBlockType;
  label: string;
  description: string;
  /** Rota sugere este formato — badge no picker, não restringe escolha. */
  recommended?: boolean;
};

const PRESENTATION_META: Record<
  Exclude<ComunicadoDataDisplayMode, "auto">,
  { label: string; description: string; blockType: ComunicadoDataBlockType }
> = {
  kpi: {
    label: "Indicador (KPI)",
    description: "Número em destaque — eficiência, totais ou percentuais.",
    blockType: "data_kpi",
  },
  table: {
    label: "Tabela",
    description: "Listagem tabular — produtos, rankings ou detalhes.",
    blockType: "data_table",
  },
  line_chart: {
    label: "Gráfico de linha",
    description: "Série temporal — evolução no período.",
    blockType: "data_chart",
  },
  bar_chart: {
    label: "Gráfico de barras",
    description: "Comparação por categorias ou buckets.",
    blockType: "data_chart",
  },
};

/** Formatos sempre disponíveis após escolher qualquer rota. */
export const UNIVERSAL_DISPLAY_MODES: Exclude<ComunicadoDataDisplayMode, "auto">[] = [
  "kpi",
  "table",
  "line_chart",
  "bar_chart",
];

export function blockTypeForDisplayMode(
  displayMode: ComunicadoDataDisplayMode,
  _suggestedDisplayModes?: string[],
): ComunicadoDataBlockType {
  if (displayMode === "auto") {
    return "data_kpi";
  }
  if (displayMode === "kpi") return "data_kpi";
  if (displayMode === "table") return "data_table";
  return "data_chart";
}

export function displayModeLabel(mode: ComunicadoDataDisplayMode): string {
  if (mode === "auto") {
    return "Automático";
  }
  return PRESENTATION_META[mode].label;
}

export function displayModeOptionLabel(option: DataPresentationOption): string {
  if (option.recommended) {
    return `${option.label} (recomendado)`;
  }
  return option.label;
}

/** Opções universais de apresentação; suggestedDisplayModes só marca recomendados. */
export function listDataPresentationOptions(
  suggestedDisplayModes?: string[] | undefined,
): DataPresentationOption[] {
  const suggested = new Set(
    (suggestedDisplayModes ?? []).map((mode) => mode.trim()).filter(Boolean),
  );

  const options = UNIVERSAL_DISPLAY_MODES.map((mode) => {
    const meta = PRESENTATION_META[mode];
    return {
      displayMode: mode,
      blockType: meta.blockType,
      label: meta.label,
      description: meta.description,
      recommended: suggested.has(mode),
    };
  });

  options.sort((left, right) => {
    if (Boolean(left.recommended) !== Boolean(right.recommended)) {
      return left.recommended ? -1 : 1;
    }
    return UNIVERSAL_DISPLAY_MODES.indexOf(left.displayMode) - UNIVERSAL_DISPLAY_MODES.indexOf(right.displayMode);
  });

  return options;
}

/** Formato padrão ao inserir bloco: última escolha do usuário ou KPI. */
export function defaultDisplayModeForInsert(
  suggestedDisplayModes: string[] | undefined,
  lastUserChoice?: ComunicadoDataDisplayMode | null,
): Exclude<ComunicadoDataDisplayMode, "auto"> {
  if (lastUserChoice && lastUserChoice !== "auto") {
    return lastUserChoice;
  }
  const suggested = (suggestedDisplayModes ?? []).map((mode) => mode.trim()).filter(Boolean);
  for (const mode of UNIVERSAL_DISPLAY_MODES) {
    if (suggested.includes(mode)) {
      return mode;
    }
  }
  return "kpi";
}
