/** Conversão de APRESENTAÇÃO de unidade para os gráficos do roteiro.
 *
 * Tempos oficiais podem ser muito pequenos (ex.: 0,0012 min) — em
 * minutos, todos os ticks do eixo colapsam para "0". Quando o maior
 * valor é menor que meio minuto, o gráfico exibe segundos (× 60),
 * sempre com a unidade explícita no eixo. O valor oficial não é
 * alterado — isto é apenas formatação de exibição. */

export type ChartTimeUnit = {
  /** Fator de conversão sobre o valor em minutos. */
  factor: number;
  /** Sufixo da unidade exibida ("min" | "s"). */
  unit: "min" | "s";
  /** Casas decimais sugeridas para ticks/rótulos. */
  decimalPlaces: number;
  /** Descrição da conversão para hints/aria. */
  note: string;
};

const MINUTE: ChartTimeUnit = {
  factor: 1,
  unit: "min",
  decimalPlaces: 4,
  note: "Valores exibidos em minutos, conforme a fonte oficial.",
};

const SECOND: ChartTimeUnit = {
  factor: 60,
  unit: "s",
  decimalPlaces: 2,
  note: "Valores convertidos para segundos apenas na exibição (1 min = 60 s) — os tempos oficiais em minutos não são alterados.",
};

/** Meio minuto: abaixo disso os ticks em minutos colapsam para zero. */
const SECONDS_THRESHOLD_MINUTES = 0.5;

export function resolveChartTimeUnit(
  valuesMinutes: readonly number[],
): ChartTimeUnit {
  const max = valuesMinutes.reduce(
    (acc, v) => (Number.isFinite(v) && v > acc ? v : acc),
    0,
  );
  return max > 0 && max < SECONDS_THRESHOLD_MINUTES ? SECOND : MINUTE;
}

export function toChartValue(
  minutes: number | null | undefined,
  unit: ChartTimeUnit,
): number | null {
  if (minutes === null || minutes === undefined) return null;
  return minutes * unit.factor;
}
