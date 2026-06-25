import type { StockValueEstimation } from "../types/supplies";
import { formatProtheusDateHuman } from "../utils/dates";
import { formatCurrency } from "../utils/format";

export type ContextStat = {
  label: string;
  value: string;
  hint?: string;
};

export function methodBadge(
  isOfficialClosure: boolean,
  isRegisterSnapshot: boolean,
  estimation?: StockValueEstimation
): { label: string; tone: "success" | "info" | "neutral" } {
  if (isOfficialClosure) {
    return { label: "Fechamento oficial SB9", tone: "success" };
  }
  if (isRegisterSnapshot) {
    return { label: "Snapshot SB2 · MATR460", tone: "info" };
  }
  if (estimation?.enabled) {
    return { label: "Kardex SB9 + SD3", tone: "neutral" };
  }
  return { label: "Posição atual SB2", tone: "info" };
}

export function buildStockEstimationStats(
  estimation: StockValueEstimation | undefined,
  isRegisterSnapshot: boolean
): ContextStat[] {
  const register = estimation?.inventory_register;
  if (isRegisterSnapshot && register) {
    const stats: ContextStat[] = [
      {
        label: "EM processo (proxy)",
        value: formatCurrency(register.em_processo_proxy_value),
      },
      {
        label: "Total geral (proxy)",
        value: formatCurrency(register.total_geral_proxy_value),
        hint: "EM estoque + EM processo",
      },
      {
        label: "Armazéns de processo",
        value: (register.process_locations ?? []).join(", ") || "—",
      },
    ];
    if (estimation?.closing_base_date) {
      stats.push({
        label: "Último fechamento SB9",
        value: formatProtheusDateHuman(estimation.closing_base_date),
        hint: estimation.closing_base_value
          ? formatCurrency(estimation.closing_base_value)
          : undefined,
      });
    }
    return stats;
  }

  if (!estimation?.enabled) return [];

  const stats: ContextStat[] = [
    {
      label: "Base SB9",
      value: formatCurrency(estimation.closing_base_value),
      hint: estimation.closing_base_date
        ? formatProtheusDateHuman(estimation.closing_base_date)
        : undefined,
    },
    {
      label: "Ponte SD3",
      value: formatCurrency(estimation.bridge_value),
    },
    {
      label: "Movimento no período",
      value: formatCurrency(estimation.period_net_value),
    },
  ];

  if (estimation.official_closure_available) {
    stats.push({
      label: "SB9 até fim do período",
      value: formatCurrency(estimation.official_closure_value),
      hint: `${formatProtheusDateHuman(estimation.official_closure_date)}${
        estimation.official_closure_on_period_end ? " · na data do inventário" : ""
      }`,
    });
  }

  return stats;
}
