import type { AppointmentRow, ByOpRow, Pagination } from "../types/appointments";
import {
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";

type AppointmentsTablesProps = {
  appointments: AppointmentRow[];
  byOp: ByOpRow[];
  listPagination: Pagination | null;
  byOpPagination: Pagination | null;
  listPage: number;
  byOpPage: number;
  onListPageChange: (page: number) => void;
  onByOpPageChange: (page: number) => void;
};

function Pager({
  pagination,
  page,
  onChange,
}: {
  pagination: Pagination | null;
  page: number;
  onChange: (page: number) => void;
}) {
  if (!pagination || pagination.total_pages <= 1) return null;
  return (
    <div className="pa-pager">
      <button
        type="button"
        className="pa-btn pa-btn--secondary"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
      >
        Anterior
      </button>
      <span className="pa-muted">
        Página {page} de {pagination.total_pages} ({formatInteger(pagination.total)}{" "}
        registros)
      </span>
      <button
        type="button"
        className="pa-btn pa-btn--secondary"
        disabled={page >= pagination.total_pages}
        onClick={() => onChange(page + 1)}
      >
        Próxima
      </button>
    </div>
  );
}

export function AppointmentsTables({
  appointments,
  byOp,
  listPagination,
  byOpPagination,
  listPage,
  byOpPage,
  onListPageChange,
  onByOpPageChange,
}: AppointmentsTablesProps) {
  return (
    <div className="pa-tables-stack">
      <section className="pa-card">
        <header className="pa-chart-card__header">
          <h2 className="pa-chart-card__title">Apontamentos</h2>
        </header>
        <div className="pa-table-wrap">
          <table className="pa-table">
            <thead>
              <tr>
                <th>Data</th>
                <th>OP</th>
                <th>Produto</th>
                <th>CT</th>
                <th className="pa-table__col--numeric">Produzida</th>
                <th className="pa-table__col--numeric">Perdida</th>
              </tr>
            </thead>
            <tbody>
              {appointments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="pa-table__empty">
                    Nenhum apontamento.
                  </td>
                </tr>
              ) : (
                appointments.map((row) => (
                  <tr key={row.appointment_id}>
                    <td>{formatProtheusDate(row.appointment_date)}</td>
                    <td>{row.production_order}</td>
                    <td>
                      {row.product}
                      {row.product_type ? ` (${row.product_type})` : ""}
                    </td>
                    <td>
                      {row.work_center}
                      {row.work_center_name ? ` — ${row.work_center_name}` : ""}
                    </td>
                    <td className="pa-table__col--numeric">
                      {formatQuantity(row.qty_produced)}
                    </td>
                    <td className="pa-table__col--numeric">
                      {formatQuantity(row.qty_lost)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pager pagination={listPagination} page={listPage} onChange={onListPageChange} />
      </section>

      <section className="pa-card">
        <header className="pa-chart-card__header">
          <h2 className="pa-chart-card__title">Por ordem de produção</h2>
        </header>
        <div className="pa-table-wrap">
          <table className="pa-table">
            <thead>
              <tr>
                <th>OP</th>
                <th>Produto</th>
                <th className="pa-table__col--numeric">Apont.</th>
                <th className="pa-table__col--numeric">CTs</th>
                <th className="pa-table__col--numeric">Produzida</th>
                <th>Período</th>
              </tr>
            </thead>
            <tbody>
              {byOp.length === 0 ? (
                <tr>
                  <td colSpan={6} className="pa-table__empty">
                    Nenhuma OP no período.
                  </td>
                </tr>
              ) : (
                byOp.map((row) => (
                  <tr key={`${row.production_order}-${row.product}`}>
                    <td>{row.production_order}</td>
                    <td>
                      {row.product}
                      {row.product_type ? ` (${row.product_type})` : ""}
                    </td>
                    <td className="pa-table__col--numeric">
                      {formatInteger(row.appointment_count)}
                    </td>
                    <td className="pa-table__col--numeric">
                      {formatInteger(row.work_center_count)}
                    </td>
                    <td className="pa-table__col--numeric">
                      {formatQuantity(row.qty_produced)}
                    </td>
                    <td>
                      {formatProtheusDate(row.first_date)} —{" "}
                      {formatProtheusDate(row.last_date)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <Pager pagination={byOpPagination} page={byOpPage} onChange={onByOpPageChange} />
      </section>
    </div>
  );
}
