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
  valueFormat?: "number" | "percent" | "compact" | "raw" | "currency";
  colorRules?: DelpiKpiColorRule[];
  /** Meta numérica para comparação / barra de progresso. */
  target?: number;
  /** Comparação: meta, período anterior (série) ou desligada. */
  comparisonMode?: "none" | "target" | "previous";
  /** Direção semântica do delta (↑ bom vs ↓ bom). Default: true. */
  higherIsBetter?: boolean;
  showComparison?: boolean;
  showProgress?: boolean;
  showSparkline?: boolean;
  comparisonLabel?: string;
};

/** Herda o tema claro do gráfico (catálogo DECK_*).
 * Ícone Gauge ligado por padrão (padrão visual do card).
 * Cores de valor/rótulo em «auto» — contraste calculado no card. */
export const DEFAULT_COMUNICADO_KPI_OPTIONS: ComunicadoKpiOptions = {
  showIcon: true,
  iconName: DECK_KPI_DEFAULTS.iconName,
  tone: "default",
  /* Número formatado (pt-BR) — raw deixa floats longos e o FitText fica miúdo no card. */
  valueFormat: "number",
  backgroundColor: DECK_KPI_DEFAULTS.backgroundColor,
  valueColor: "auto",
  comparisonMode: "none",
  higherIsBetter: true,
  showComparison: false,
  showProgress: false,
  showSparkline: false,
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
