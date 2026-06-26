import type { TableExportPayload } from "./types";
import { formatPercent } from "../utils/format";

type PercentIndicatorRow = {
  name: string;
  value: number;
};

export function buildPercentIndicatorsExportPayload(
  rows: PercentIndicatorRow[],
): TableExportPayload {
  return {
    title: "Indicadores percentuais",
    columns: [
      { key: "indicador", label: "Indicador" },
      { key: "valor", label: "Valor (%)" },
    ],
    rows: rows.map((row) => ({
      indicador: row.name,
      valor: formatPercent(row.value),
    })),
  };
}
