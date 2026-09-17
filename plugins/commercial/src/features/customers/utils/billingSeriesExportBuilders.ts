import type { TableExportPayload } from "@delpi/plugin-ui/index";

import {
  includesQuantityMetric,
  type PortfolioBillingMetric,
} from "../../../content/billingMetric";
import { formatCurrency, formatQuantity } from "../../../utils/format";

type BillingSeriesExportPoint = {
  periodo: string;
  faturamento: number;
  quantidade?: number | null;
  faturamento_prior?: number | null;
  faturamento_prior_2?: number | null;
  faturamento_prior_3?: number | null;
};

function formatPrimaryAmount(
  value: number,
  metric: PortfolioBillingMetric,
): string {
  return metric === "quantity" ? formatQuantity(value) : formatCurrency(value);
}

function formatOptionalPrimary(
  value: number | null | undefined,
  metric: PortfolioBillingMetric,
): string {
  if (value == null) return "—";
  return formatPrimaryAmount(value, metric);
}

export function buildBillingSeriesExportPayload(
  points: readonly BillingSeriesExportPoint[],
  options: {
    title: string;
    compareYears?: number;
    metric?: PortfolioBillingMetric;
  } = { title: "Faturamento" },
): TableExportPayload {
  const years = options.compareYears ?? 0;
  const metric = options.metric ?? "value";
  const showQuantityOverlay = includesQuantityMetric(metric) && metric === "both";
  const primaryLabel = metric === "quantity" ? "Quantidade" : "Faturamento";
  const columns = [
    { key: "periodo", label: "Período" },
    { key: "faturamento", label: primaryLabel },
    ...(showQuantityOverlay ? [{ key: "quantidade", label: "Quantidade" }] : []),
    ...(years >= 1 ? [{ key: "prior1", label: "Ano ant." }] : []),
    ...(years >= 2 ? [{ key: "prior2", label: "−2 anos" }] : []),
    ...(years >= 3 ? [{ key: "prior3", label: "−3 anos" }] : []),
  ];
  return {
    title: options.title,
    columns,
    rows: points.map((point) => ({
      periodo: point.periodo,
      faturamento: formatPrimaryAmount(point.faturamento, metric),
      ...(showQuantityOverlay
        ? { quantidade: formatQuantity(Number(point.quantidade) || 0) }
        : {}),
      ...(years >= 1
        ? {
            prior1: formatOptionalPrimary(point.faturamento_prior, metric),
          }
        : {}),
      ...(years >= 2
        ? {
            prior2: formatOptionalPrimary(point.faturamento_prior_2, metric),
          }
        : {}),
      ...(years >= 3
        ? {
            prior3: formatOptionalPrimary(point.faturamento_prior_3, metric),
          }
        : {}),
    })),
  };
}

export function buildPurchaseEvolutionExportPayload(
  points: ReadonlyArray<{ periodo: string; atual: number; anterior: number }>,
): TableExportPayload {
  return {
    title: "Evolução de compras",
    columns: [
      { key: "periodo", label: "Período" },
      { key: "atual", label: "Período atual" },
      { key: "anterior", label: "Período anterior" },
    ],
    rows: points.map((point) => ({
      periodo: point.periodo,
      atual: formatCurrency(point.atual),
      anterior: formatCurrency(point.anterior),
    })),
  };
}
