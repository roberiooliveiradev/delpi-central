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

/**
 * Indicadores: AS-IS / TO-BE são dados da revisão; Δ é CALCULADO (apresentação).
 * Provenance fica nos headers — não no nome de cada métrica.
 */
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
        title="Sem indicadores"
        defaultMessage="Não há indicadores informados para este cenário."
      />
    );
  }

  if (!hasAsIsMeasurement && !hasToBeMeasurement) {
    return (
      <EmptyState
        classNames={EMPTY}
        title="Sem indicadores"
        defaultMessage="Não há indicadores informados para este cenário."
      />
    );
  }

  return (
    <div className="tm-processo-results-table-scroll tm-measurement-compare">
      <DataTable
        columns={[
          {
            key: "metric",
            header: "Métrica",
            render: (row: MeasurementCompareRow) => (
              <span className="tm-measurement-compare__metric">
                <span className="tm-measurement-compare__metric-name">{row.label}</span>
                <span className="tm-measurement-compare__unit">({row.unitHint})</span>
              </span>
            ),
          },
          {
            key: "asis",
            header: pairMode ? "AS-IS · INFORMADO" : "Valor · INFORMADO",
            render: (row) =>
              row.asIsValue == null ? "—" : formatProcessoNumber(row.asIsValue),
          },
          {
            key: "tobe",
            header: "TO-BE · PROPOSTO",
            render: (row) =>
              row.toBeValue == null ? "—" : formatProcessoNumber(row.toBeValue),
          },
          {
            key: "delta",
            header: "Δ · CALCULADO",
            render: (row) => {
              if (row.delta == null) return "—";
              const signed =
                row.delta > 0
                  ? `+${formatProcessoNumber(row.delta)}`
                  : formatProcessoNumber(row.delta);
              return <span className="tm-measurement-compare__delta">{signed}</span>;
            },
          },
        ]}
        rows={rows}
        rowKey={(row) => row.id}
      />
      {pairMode ? (
        <p className="tm-measurement-compare__caption">
          AS-IS e TO-BE vêm das revisões. Δ é diferença numérica de apresentação — sem classificar
          ganho ou perda.
        </p>
      ) : null}
    </div>
  );
}
