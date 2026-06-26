import { formatDisplayDate } from "../utils/dates";
import { OPERATIONAL_UNIT_COLUMN_LABEL } from "../utils/operationalUnitLabels";

export type PrintReportSummaryProps = {
  title: string;
  dateStart: string;
  dateEnd: string;
  branchLabel?: string;
};

export function PrintReportSummary({
  title,
  dateStart,
  dateEnd,
  branchLabel,
}: PrintReportSummaryProps) {
  const printedAt = new Date().toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });

  return (
    <section className="dc-print-summary dc-print-only" aria-hidden="true">
      <h2 className="dc-print-summary__title">{title}</h2>
      <dl className="dc-print-summary__meta">
        <div>
          <dt>Período</dt>
          <dd>
            {formatDisplayDate(dateStart)} — {formatDisplayDate(dateEnd)}
          </dd>
        </div>
        <div>
          <dt>{OPERATIONAL_UNIT_COLUMN_LABEL}</dt>
          <dd>{branchLabel?.trim() ? branchLabel : "Todas"}</dd>
        </div>
        <div>
          <dt>Emitido em</dt>
          <dd>{printedAt}</dd>
        </div>
      </dl>
    </section>
  );
}
