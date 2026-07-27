import { createDashboardStatusBadge, dataTableBemClasses } from "@delpi/plugin-ui/index";

import type { ProductionOeeRoutingOperation } from "../types/productionOeeDetail";
import { formatHours, formatInteger } from "../utils/format";

const EF_TABLE = dataTableBemClasses("ef");
const EfStatusBadge = createDashboardStatusBadge({ prefix: "ef" });

type RoutingOperationsTableProps = {
  operations: ProductionOeeRoutingOperation[];
};

export function RoutingOperationsTable({ operations }: RoutingOperationsTableProps) {
  return (
    <section className="ef-table-card" aria-label="Roteiro de produção">
      <header className="ef-table-card__header">
        <div>
          <h2>Roteiro de produção</h2>
          <p>SG2010 — operação do apontamento destacada</p>
        </div>
      </header>

      <div className={EF_TABLE.wrap}>
        <table className={`${EF_TABLE.table} ef-table--routing`}>
          <thead>
            <tr>
              <th className="ef-table__col--compact">Operação</th>
              <th className={EF_TABLE.colWide}>Descrição</th>
              <th className="ef-table__col--compact">CT</th>
              <th className="ef-table__col--compact">Recurso</th>
              <th className={EF_TABLE.colNumeric}>Setup (h)</th>
              <th className={EF_TABLE.colNumeric}>Tempo padrão (h/peça)</th>
              <th className={EF_TABLE.colNumeric}>Nível BOM</th>
              <th className="ef-table__col--badge">Apontamento</th>
            </tr>
          </thead>
          <tbody>
            {operations.length === 0 ? (
              <tr>
                <td colSpan={8} className={EF_TABLE.empty}>
                  Roteiro não encontrado para o produto.
                </td>
              </tr>
            ) : (
              operations.map((row, index) => (
                <tr key={`${row.operation_code ?? "op"}-${index}`}>
                  <td className="ef-table__col--compact" data-label="Operação">
                    {row.operation_code ?? "—"}
                  </td>
                  <td className={EF_TABLE.colWide} data-label="Descrição">
                    {row.operation_description ?? "—"}
                  </td>
                  <td className="ef-table__col--compact" data-label="CT">
                    {row.work_center ?? "—"}
                  </td>
                  <td className="ef-table__col--compact" data-label="Recurso">
                    {row.resource_code ?? "—"}
                  </td>
                  <td className={EF_TABLE.colNumeric} data-label="Setup (h)">
                    {formatHours(row.setup_hours ?? null, 3)}
                  </td>
                  <td className={EF_TABLE.colNumeric} data-label="Tempo padrão (h/peça)">
                    {formatHours(row.standard_time_hours_piece ?? null, 3)}
                  </td>
                  <td className={EF_TABLE.colNumeric} data-label="Nível BOM">
                    {formatInteger(row.bom_level ?? null)}
                  </td>
                  <td className="ef-table__col--badge" data-label="Apontamento">
                    {row.is_appointment_operation ? (
                      <EfStatusBadge label="Operação atual" variant="success" />
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
