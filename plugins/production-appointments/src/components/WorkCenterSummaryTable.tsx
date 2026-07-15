import type { WorkCenterSummaryRow } from "../types/appointments";
import { formatInteger, formatQuantity } from "../utils/formatters";

type WorkCenterSummaryTableProps = {
  items: WorkCenterSummaryRow[];
};

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

export function WorkCenterSummaryTable({ items }: WorkCenterSummaryTableProps) {
  return (
    <section className="pa-card">
      <header className="pa-chart-card__header">
        <h2 className="pa-chart-card__title">Resumo por centro de trabalho</h2>
      </header>
      <div className="pa-table-wrap">
        <table className="pa-table">
          <thead>
            <tr>
              <th>CT</th>
              <th>Nome</th>
              <th className="pa-table__col--numeric">Apont.</th>
              <th className="pa-table__col--numeric">Produzida</th>
              <th className="pa-table__col--numeric">Perdida</th>
              <th className="pa-table__col--numeric">OPs</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={6} className="pa-table__empty">
                  Nenhum apontamento no período.
                </td>
              </tr>
            ) : (
              items.map((row) => (
                <tr key={row.work_center}>
                  <td>
                    {row.work_center}
                    {isInspection(row.is_final_inspection) ? (
                      <span className="pa-badge">Inspeção final</span>
                    ) : null}
                  </td>
                  <td>{row.work_center_name}</td>
                  <td className="pa-table__col--numeric">
                    {formatInteger(row.appointment_count)}
                  </td>
                  <td className="pa-table__col--numeric">
                    {formatQuantity(row.qty_produced)}
                  </td>
                  <td className="pa-table__col--numeric">
                    {formatQuantity(row.qty_lost)}
                  </td>
                  <td className="pa-table__col--numeric">{formatInteger(row.op_count)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
