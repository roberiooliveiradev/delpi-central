import {
  DECK_KPI_DEFAULTS,
  type DelpiKpiCardTone,
  type DelpiKpiColorRule,
} from "@delpi/plugin-ui/index";

/** Opções declarativas do bloco `kpi_view` (espelha chartOptions). */
export type ComunicadoKpiOptions = {
  title?: string;
  subtitle?: string;
  unit?: string;
  iconName?: string;
  showIcon?: boolean;
  showTitle?: boolean;
  tone?: DelpiKpiCardTone;
  valueColor?: string;
  backgroundColor?: string;
  valueFormat?: "number" | "percent" | "compact" | "raw";
  colorRules?: DelpiKpiColorRule[];
};

/** Herda o tema claro do gráfico (catálogo DECK_*). */
export const DEFAULT_COMUNICADO_KPI_OPTIONS: ComunicadoKpiOptions = {
  showIcon: true,
  tone: "default",
  valueFormat: "raw",
  backgroundColor: DECK_KPI_DEFAULTS.backgroundColor,
  valueColor: DECK_KPI_DEFAULTS.valueColor,
};

export function mergeComunicadoKpiOptions(
  partial?: ComunicadoKpiOptions | null,
): ComunicadoKpiOptions {
  return {
    ...DEFAULT_COMUNICADO_KPI_OPTIONS,
    ...(partial ?? {}),
    colorRules: partial?.colorRules ? [...partial.colorRules] : undefined,
  };
}
