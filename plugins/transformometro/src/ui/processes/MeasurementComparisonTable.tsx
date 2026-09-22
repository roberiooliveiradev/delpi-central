import { EmptyState, emptyStateCardBemClasses } from "@delpi/plugin-ui/index";

import { DataTable } from "../../components/DataTable";
import { formatProcessoNumber } from "../../utils/processoDetailTables";
import type { MeasurementCompareRow } from "./buildRevisionComparisonView";

const EMPTY = emptyStateCardBemClasses("ds");

type Props = {
  rows: MeasurementCompareRow[];
  hasAsIsMeasurement: boolean;
  hasToBeMeasurement: boolean;
  pairMode: boolean;
};

export function MeasurementComparisonTable({
  rows,
  hasAsIsMeasurement,
  hasToBeMeasurement,
  pairMode,
}: Props) {
  if (pairMode && !hasToBeMeasurement) {
    return (
      <EmptyState
        classNames={EMPTY}
        title="Sem medição no cenário"
        defaultMessage="Sem medição informada para este cenário."
      />
    );
  }

  if (!hasAsIsMeasurement && !hasToBeMeasurement) {
    return (
      <EmptyState
        classNames={EMPTY}
        title="Sem medição"
        defaultMessage="Sem medição informada para este cenário."
      />
    );
  }

  return (
    <div className="tm-processo-results-table-scroll">
      <DataTable
        columns={[
          {
            key: "metric",
            header: "Métrica",
            render: (row: MeasurementCompareRow) => (
              <span>
                {row.label}
                <span className="ds-hint"> ({row.unitHint})</span>
              </span>
            ),
          },
          {
            key: "asis",
            header: "AS-IS",
            render: (row) =>
              row.asIsValue == null ? "—" : formatProcessoNumber(row.asIsValue),
          },
          {
            key: "tobe",
            header: "TO-BE",
            render: (row) =>
              row.toBeValue == null ? "—" : formatProcessoNumber(row.toBeValue),
          },
          {
            key: "delta",
            header: "Delta",
            render: (row) => {
              if (row.delta == null) return "—";
              const signed = row.delta > 0 ? `+${formatProcessoNumber(row.delta)}` : formatProcessoNumber(row.delta);
              return signed;
            },
          },
          {
            key: "nature",
            header: "Natureza",
            render: (row) =>
              row.deltaKind === "CALCULATED_PRESENTATION" ? "CALCULADO (apresentação)" : "—",
          },
        ]}
        rows={rows}
        rowKey={(row) => row.id}
      />
      <p className="ds-hint">
        Delta é diferença aritmética de apresentação quando AS-IS e TO-BE têm a mesma unidade. Não
        classifica automaticamente ganho ou perda.
      </p>
    </div>
  );
}
