import type { TableExportPayload } from "@delpi/plugin-ui/index";

import {
  formatQuantityWithUnit,
  includesQuantityMetric,
  type PortfolioBillingMetric,
} from "../../../content/billingMetric";
import { formatCurrency } from "../../../utils/format";

type BillingSeriesExportPoint = {
  periodo: string;
  faturamento: number;
  quantidade?: number | null;
  faturamento_prior?: number | null;
  faturamento_prior_2?: number | null;
  faturamento_prior_3?: number | null;
  quantidade_prior?: number | null;
  quantidade_prior_2?: number | null;
  quantidade_prior_3?: number | null;
};

function formatPrimaryAmount(
  value: number,
  metric: PortfolioBillingMetric,
  unit?: string | null,
  mixed?: boolean,
): string {
  return metric === "quantity"
    ? formatQuantityWithUnit(value, unit, mixed)
    : formatCurrency(value);
}

function formatOptionalPrimary(
  value: number | null | undefined,
  metric: PortfolioBillingMetric,
  unit?: string | null,
  mixed?: boolean,
): string {
  if (value == null) return "—";
  return formatPrimaryAmount(value, metric, unit, mixed);
}

export function buildBillingSeriesExportPayload(
  points: readonly BillingSeriesExportPoint[],
  options: {
    title: string;
    compareYears?: number;
    metric?: PortfolioBillingMetric;
    unit?: string | null;
    mixedUnits?: boolean;
  } = { title: "Faturamento" },
): TableExportPayload {
  const years = options.compareYears ?? 0;
  const metric = options.metric ?? "value";
  const unit = options.unit;
  const mixed = Boolean(options.mixedUnits);
  const showQuantityOverlay = includesQuantityMetric(metric) && metric === "both";
  const primaryLabel = metric === "quantity" ? "Quantidade" : "Faturamento";
  const columns = [
    { key: "periodo", label: "Período" },
    { key: "faturamento", label: primaryLabel },
    ...(showQuantityOverlay ? [{ key: "quantidade", label: "Quantidade" }] : []),
    ...(years >= 1 ? [{ key: "prior1", label: "Ano ant." }] : []),
    ...(showQuantityOverlay && years >= 1
      ? [{ key: "qtyPrior1", label: "Qtd ano ant." }]
      : []),
    ...(years >= 2 ? [{ key: "prior2", label: "−2 anos" }] : []),
    ...(showQuantityOverlay && years >= 2
      ? [{ key: "qtyPrior2", label: "Qtd −2 anos" }]
      : []),
    ...(years >= 3 ? [{ key: "prior3", label: "−3 anos" }] : []),
    ...(showQuantityOverlay && years >= 3
      ? [{ key: "qtyPrior3", label: "Qtd −3 anos" }]
      : []),
  ];
  return {
    title: options.title,
    columns,
    rows: points.map((point) => ({
      periodo: point.periodo,
      faturamento: formatPrimaryAmount(point.faturamento, metric, unit, mixed),
      ...(showQuantityOverlay
        ? {
            quantidade: formatQuantityWithUnit(
              Number(point.quantidade) || 0,
              unit,
              mixed,
            ),
          }
        : {}),
      ...(years >= 1
        ? {
            prior1: formatOptionalPrimary(point.faturamento_prior, metric, unit, mixed),
          }
        : {}),
      ...(showQuantityOverlay && years >= 1
        ? {
            qtyPrior1:
              point.quantidade_prior == null
                ? "—"
                : formatQuantityWithUnit(Number(point.quantidade_prior) || 0, unit, mixed),
          }
        : {}),
      ...(years >= 2
        ? {
            prior2: formatOptionalPrimary(
              point.faturamento_prior_2,
              metric,
              unit,
              mixed,
            ),
          }
        : {}),
      ...(showQuantityOverlay && years >= 2
        ? {
            qtyPrior2:
              point.quantidade_prior_2 == null
                ? "—"
                : formatQuantityWithUnit(
                    Number(point.quantidade_prior_2) || 0,
                    unit,
                    mixed,
                  ),
          }
        : {}),
      ...(years >= 3
        ? {
            prior3: formatOptionalPrimary(
              point.faturamento_prior_3,
              metric,
              unit,
              mixed,
            ),
          }
        : {}),
      ...(showQuantityOverlay && years >= 3
        ? {
            qtyPrior3:
              point.quantidade_prior_3 == null
                ? "—"
                : formatQuantityWithUnit(
                    Number(point.quantidade_prior_3) || 0,
                    unit,
                    mixed,
                  ),
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
