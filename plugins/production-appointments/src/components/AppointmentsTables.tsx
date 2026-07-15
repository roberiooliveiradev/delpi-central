import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { AppointmentRow, ByOpRow, Pagination as PaginationMeta } from "../types/appointments";
import {
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";
import { ChartCard } from "./ChartCard";
import { Pagination } from "./Pagination";

type AppointmentsTablesProps = {
  appointments: AppointmentRow[];
  byOp: ByOpRow[];
  listPagination: PaginationMeta | null;
  byOpPagination: PaginationMeta | null;
  listPage: number;
  byOpPage: number;
  pageSize: number;
  onListPageChange: (page: number) => void;
  onByOpPageChange: (page: number) => void;
};

export function AppointmentsTables({
  appointments,
  byOp,
  listPagination,
  byOpPagination,
  listPage,
  byOpPage,
  pageSize,
  onListPageChange,
  onByOpPageChange,
}: AppointmentsTablesProps) {
  return (
    <div className="pa-tables-stack">
      <ChartCard title="Apontamentos" titleHint={PA_HELP_TOOLTIPS.tables.appointments}>
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
        {listPagination ? (
          <Pagination
            page={listPage}
            pageSize={pageSize}
            total={listPagination.total}
            totalPages={listPagination.total_pages}
            onPageChange={onListPageChange}
          />
        ) : null}
      </ChartCard>

      <ChartCard title="Por ordem de produção" titleHint={PA_HELP_TOOLTIPS.tables.byOp}>
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
        {byOpPagination ? (
          <Pagination
            page={byOpPage}
            pageSize={pageSize}
            total={byOpPagination.total}
            totalPages={byOpPagination.total_pages}
            onPageChange={onByOpPageChange}
          />
        ) : null}
      </ChartCard>
    </div>
  );
}
