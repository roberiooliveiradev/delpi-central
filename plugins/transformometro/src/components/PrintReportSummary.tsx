import { formatDisplayDate } from "../utils/dates";

export type PrintReportSummaryProps = {
  title: string;
  dateStart: string;
  dateEnd: string;
  branchLabel?: string;
  setorLabel?: string;
};

export function PrintReportSummary({
  title,
  dateStart,
  dateEnd,
  branchLabel = "Consolidado",
  setorLabel = "Todos",
}: PrintReportSummaryProps) {
  const printedAt = new Date().toLocaleString("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  });

  return (
    <section className="ds-print-summary ds-print-only" aria-hidden="true">
      <h2 className="ds-print-summary__title">{title}</h2>
      <dl className="ds-print-summary__meta">
        <div>
          <dt>Período</dt>
          <dd>
            {formatDisplayDate(dateStart)} — {formatDisplayDate(dateEnd)}
          </dd>
        </div>
        <div>
          <dt>Filial</dt>
          <dd>{branchLabel}</dd>
        </div>
        <div>
          <dt>Setor</dt>
          <dd>{setorLabel}</dd>
        </div>
        <div>
          <dt>Emitido em</dt>
          <dd>{printedAt}</dd>
        </div>
      </dl>
    </section>
  );
}
