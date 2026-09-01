import type {
  BillingCustomer,
  BillingLine,
  BillingSeriesPoint,
  FinancialBranch,
} from "../types";

const PIE_LABEL_MAX = 22;

export function clampPercent(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

export function billingSeriesKeys(branch: FinancialBranch): Array<"rol01" | "rol02"> {
  if (branch === "01") return ["rol01"];
  if (branch === "02") return ["rol02"];
  return ["rol01", "rol02"];
}

export function waterfallPeak(lines: BillingLine[]): number {
  const values = lines.map((line) => Math.abs(line.value)).filter((value) => value > 0);
  return values.length ? Math.max(...values) : 0;
}

export function waterfallBarWidth(value: number, peak: number): number {
  if (!(peak > 0) || !Number.isFinite(value)) return 0;
  const ratio = (Math.abs(value) / peak) * 100;
  if (ratio <= 0) return 0;
  return Math.min(100, Math.max(6, ratio));
}

export function seriesChartRows(items: BillingSeriesPoint[]): Array<Record<string, string | number>> {
  return items.map((point) => ({
    periodo: point.period || point.sortKey,
    rol01: point.rol01,
    rol02: point.rol02,
  }));
}

export type BillingCustomerPieRow = {
  label: string;
  rol: number;
  fill: string;
};

/** Fatias do ranking de clientes (itens + demais) para o gráfico de pizza do kit. */
export function customerPieRows(
  items: readonly BillingCustomer[],
  others: BillingCustomer | null | undefined,
  othersLabel: string,
  palette: readonly string[],
): BillingCustomerPieRow[] {
  const seen = new Set<string>();
  const rows: BillingCustomerPieRow[] = [];
  const colorAt = (index: number) =>
    palette.length ? palette[index % palette.length]! : "var(--fin-accent, #089bdb)";

  const push = (item: BillingCustomer, forcedLabel?: string) => {
    if (!(item.rol > 0)) return;
    const base = (forcedLabel ?? item.customerName ?? item.customerCode).trim() || item.customerCode;
    const label =
      !forcedLabel && seen.has(base) && item.customerStore
        ? `${base} · ${item.customerStore}`
        : base;
    if (!forcedLabel) seen.add(base);
    rows.push({
      label: truncatePieLabel(label),
      rol: item.rol,
      fill: colorAt(rows.length),
    });
  };

  for (const item of items) {
    push(item);
  }
  if (others) {
    push(others, othersLabel);
  }
  return rows;
}

function truncatePieLabel(label: string): string {
  if (label.length <= PIE_LABEL_MAX) return label;
  return `${label.slice(0, PIE_LABEL_MAX - 1).trimEnd()}…`;
}

export type CompositionStatementRole = "add" | "subtract" | "result";

export type CompositionStatementRow = {
  key: string;
  label: string;
  role: CompositionStatementRole;
  movement: number;
  balance: number;
};

/** Linhas de demonstração: movimento e saldo acumulado até a ROL. */
export function compositionStatementRows(lines: readonly BillingLine[]): CompositionStatementRow[] {
  let balance = 0;
  return lines.map((line) => {
    const role: CompositionStatementRole =
      line.role === "subtract" || line.role === "result" ? line.role : "add";
    if (role === "add") {
      balance += line.value;
    } else if (role === "subtract") {
      balance -= Math.abs(line.value);
    } else {
      balance = line.value;
    }
    return {
      key: line.key,
      label: line.label,
      role,
      movement: line.value,
      balance,
    };
  });
}
