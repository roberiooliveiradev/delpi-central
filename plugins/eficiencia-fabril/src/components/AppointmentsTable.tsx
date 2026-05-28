import type { EficienciaFabrilItem } from "../types/eficienciaFabril";
import { formatCurrency, formatPercent } from "../utils/format";
import { formatDisplayDate } from "../utils/dates";

type AppointmentsTableProps = {
  items: EficienciaFabrilItem[];
  page: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function AppointmentsTable({
  items,
  page,
  totalPages,
  total,
  onPageChange,
}: AppointmentsTableProps) {
  return (
    <section className="ef-table-card" aria-label="Apontamentos">
      <header className="ef-table-card__header">
        <div>
          <h2>Apontamentos</h2>
          <p>{total.toLocaleString("pt-BR")} registro(s) no período</p>
        </div>
        <div className="ef-pagination">
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            Anterior
          </button>
          <span>
            Página {page} de {Math.max(totalPages, 1)}
          </span>
          <button
            type="button"
            className="ef-btn ef-btn--ghost"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            Próxima
          </button>
        </div>
      </header>

      <div className="ef-table-wrap">
        <table className="ef-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Filial</th>
              <th>OP</th>
              <th>CT</th>
              <th>Operador</th>
              <th>Eficiência</th>
              <th>Resultado MOD</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={8} className="ef-table__empty">
                  Nenhum apontamento para os filtros selecionados.
                </td>
              </tr>
            ) : (
              items.map((item, index) => (
                <tr key={`${item.op}-${item.data_producao}-${index}`}>
                  <td>{formatDisplayDate(item.data_producao)}</td>
                  <td>{item.filial ?? "—"}</td>
                  <td>{item.op ?? "—"}</td>
                  <td>{item.centro_trabalho ?? "—"}</td>
                  <td>{item.nome_operador ?? item.login_operador ?? "—"}</td>
                  <td>{formatPercent(item.eficiencia_percentual)}</td>
                  <td>{formatCurrency(item.resultado_mod)}</td>
                  <td>
                    <span className="ef-badge">{item.status_registro ?? "—"}</span>
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
