import { EmptyState, emptyStateCardBemClasses, HelpTooltip } from "@delpi/plugin-ui/index";

import { DataTable } from "../../components/DataTable";
import { TmStatusBadge } from "../../components/tmChromeUi";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { formatProcessoNumber } from "../../utils/processoDetailTables";
import type { MeasurementCompareRow } from "./buildRevisionComparisonView";

const EMPTY = emptyStateCardBemClasses("ds");
const H = TM_HELP_TOOLTIPS.resultados;

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
                {row.deltaKind === "CALCULATED_PRESENTATION" ? (
                  <span className="tm-measurement-compare__nature">
                    <TmStatusBadge label="CALCULADO" variant="neutral" />
                    <HelpTooltip content={H.calculado} ariaLabel="Ajuda: CALCULADO" />
                  </span>
                ) : null}
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
            header: "Δ",
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
    </div>
  );
}
