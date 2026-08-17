import type { TableExportPayload } from "@delpi/plugin-ui/index";

import { formatCurrency } from "../../../utils/format";

type BillingSeriesExportPoint = {
  periodo: string;
  faturamento: number;
  faturamento_prior?: number | null;
  faturamento_prior_2?: number | null;
  faturamento_prior_3?: number | null;
};

export function buildBillingSeriesExportPayload(
  points: readonly BillingSeriesExportPoint[],
  options: { title: string; compareYears?: number } = { title: "Faturamento" },
): TableExportPayload {
  const years = options.compareYears ?? 0;
  const columns = [
    { key: "periodo", label: "Período" },
    { key: "faturamento", label: "Faturamento" },
    ...(years >= 1 ? [{ key: "prior1", label: "Ano ant." }] : []),
    ...(years >= 2 ? [{ key: "prior2", label: "−2 anos" }] : []),
    ...(years >= 3 ? [{ key: "prior3", label: "−3 anos" }] : []),
  ];
  return {
    title: options.title,
    columns,
    rows: points.map((point) => ({
      periodo: point.periodo,
      faturamento: formatCurrency(point.faturamento),
      ...(years >= 1
        ? {
            prior1:
              point.faturamento_prior == null
                ? "—"
                : formatCurrency(point.faturamento_prior),
          }
        : {}),
      ...(years >= 2
        ? {
            prior2:
              point.faturamento_prior_2 == null
                ? "—"
                : formatCurrency(point.faturamento_prior_2),
          }
        : {}),
      ...(years >= 3
        ? {
            prior3:
              point.faturamento_prior_3 == null
                ? "—"
                : formatCurrency(point.faturamento_prior_3),
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
