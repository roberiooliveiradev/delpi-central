import { defaultDataBlockTypeForRoute } from "./comunicadoHelpers";
import type {
  ComunicadoDataBlockType,
  ComunicadoDataDisplayMode,
} from "./comunicadoTypes";

export type DataPresentationOption = {
  displayMode: ComunicadoDataDisplayMode;
  blockType: ComunicadoDataBlockType;
  label: string;
  description: string;
};

const PRESENTATION_META: Record<
  Exclude<ComunicadoDataDisplayMode, "auto">,
  { label: string; description: string; blockType: ComunicadoDataBlockType }
> = {
  kpi: {
    label: "Valor destacado (KPI)",
    description: "Número em destaque — eficiência, totais ou percentuais.",
    blockType: "data_kpi",
  },
  table: {
    label: "Listagem (tabela)",
    description: "Lista compacta — produtos, rankings TOP N.",
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

const MODE_ORDER: ComunicadoDataDisplayMode[] = [
  "auto",
  "kpi",
  "table",
  "line_chart",
  "bar_chart",
];

export function blockTypeForDisplayMode(
  displayMode: ComunicadoDataDisplayMode,
  allowedDisplayModes?: string[],
): ComunicadoDataBlockType {
  if (displayMode === "auto") {
    return defaultDataBlockTypeForRoute(allowedDisplayModes);
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

/** Opções de apresentação permitidas para uma rota do catálogo TV. */
export function listDataPresentationOptions(
  allowedDisplayModes: string[] | undefined,
): DataPresentationOption[] {
  const allowed = new Set((allowedDisplayModes ?? []).map((mode) => mode.trim()).filter(Boolean));
  const options: DataPresentationOption[] = [];

  for (const mode of MODE_ORDER) {
    if (mode !== "auto" && !allowed.has(mode)) continue;
    if (mode === "auto" && !allowed.has("auto") && allowed.size > 0) continue;

    if (mode === "auto") {
      options.push({
        displayMode: "auto",
        blockType: defaultDataBlockTypeForRoute(allowedDisplayModes),
        label: "Automático",
        description: "Escolhe KPI, gráfico ou listagem conforme a rota.",
      });
      continue;
    }

    const meta = PRESENTATION_META[mode];
    options.push({
      displayMode: mode,
      blockType: meta.blockType,
      label: meta.label,
      description: meta.description,
    });
  }

  if (options.length === 0) {
    return [
      {
        displayMode: "auto",
        blockType: defaultDataBlockTypeForRoute(allowedDisplayModes),
        label: "Automático",
        description: "Formato padrão para esta rota.",
      },
    ];
  }

  return options;
}
