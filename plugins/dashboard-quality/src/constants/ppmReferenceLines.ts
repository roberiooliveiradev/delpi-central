import type { PpmType } from "../types/ppm";

export type PpmReferenceConfig = {
  /** Meta desejada (linha tracejada verde). */
  target: number | null;
  /** Limite máximo tolerado (linha tracejada vermelha). */
  limit: number | null;
};

/**
 * Metas/limites exibidos como linhas de referência nos gráficos PPM.
 * Ajuste aqui ou via variáveis VITE_DQ_PPM_* no `.env` do plugin.
 */
export const PPM_REFERENCE_LINES: Record<PpmType | "compare", PpmReferenceConfig> =
  {
    internal: { target: null, limit: null },
    external: { target: null, limit: null },
    compare: { target: null, limit: null },
  };

export type PpmChartReferenceLine = {
  value: number;
  label: string;
  stroke: string;
  strokeDasharray?: string;
};

function readEnvNumber(key: string): number | null {
  const raw = import.meta.env[key];
  if (raw === undefined || raw === "") return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

function resolveConfig(
  mode: PpmType | "compare"
): PpmReferenceConfig {
  const base = PPM_REFERENCE_LINES[mode];
  const suffix = mode === "compare" ? "COMPARE" : mode.toUpperCase();

  return {
    target:
      readEnvNumber(`VITE_DQ_PPM_TARGET_${suffix}`) ??
      readEnvNumber("VITE_DQ_PPM_TARGET") ??
      base.target,
    limit:
      readEnvNumber(`VITE_DQ_PPM_LIMIT_${suffix}`) ??
      readEnvNumber("VITE_DQ_PPM_LIMIT") ??
      base.limit,
  };
}

export function getPpmChartReferenceLines(
  mode: PpmType | "compare"
): PpmChartReferenceLine[] {
  const { target, limit } = resolveConfig(mode);
  const lines: PpmChartReferenceLine[] = [];

  if (target !== null) {
    lines.push({
      value: target,
      label: "Meta",
      stroke: "#2e7d32",
      strokeDasharray: "6 4",
    });
  }

  if (limit !== null) {
    lines.push({
      value: limit,
      label: "Limite",
      stroke: "#c62828",
      strokeDasharray: "4 4",
    });
  }

  return lines;
}
