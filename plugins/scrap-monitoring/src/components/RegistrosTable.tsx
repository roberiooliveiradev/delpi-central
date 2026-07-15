import type { ScrapRegistroItem } from "../types/scrap";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatQuantity,
} from "../utils/formatters";
import { Pagination } from "./Pagination";

type RegistrosTableProps = {
  items: ScrapRegistroItem[];
  loading?: boolean;
  page: number;
  pageSize: number;
  totalPages: number;
  total: number;
  onPageChange: (page: number) => void;
};

export function RegistrosTable({
  items,
  loading = false,
  page,
  pageSize,
  totalPages,
  total,
  onPageChange,
}: RegistrosTableProps) {
  return (
    <section className="sm-table-card sm-card">
      <header className="sm-table-card__header">
        <h2 className="sm-table-card__title">Registros de refugo</h2>
        <p className="sm-table-card__meta">
          {loading ? "Carregando…" : `${total} registro(s)`}
        </p>
      </header>
      <div className="sm-table-wrap">
        <table className="sm-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>OP</th>
              <th>PA</th>
              <th>MP</th>
              <th>Descrição</th>
              <th>Motivo</th>
              <th>CT</th>
              <th>Colaborador</th>
              <th className="sm-table__col--numeric">Qtd</th>
              <th className="sm-table__col--numeric">Valor</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && !loading ? (
              <tr>
                <td colSpan={10} className="sm-table__empty">
                  Nenhum registro no período.
                </td>
              </tr>
            ) : (
              items.map((item, index) => (
                <tr key={`${item.op}-${item.mp}-${item.dataPerda}-${index}`}>
                  <td>{formatDatePtBr(item.dataPerda)}</td>
                  <td>{item.op || "—"}</td>
                  <td>{item.pa || "—"}</td>
                  <td>{item.mp || "—"}</td>
                  <td>{item.descricao || "—"}</td>
                  <td>{item.motivo || item.motivoCodigo || "—"}</td>
                  <td>{item.centroTrabalho || "—"}</td>
                  <td>{item.nomeOperador || item.codigoOperador || "—"}</td>
                  <td className="sm-table__col--numeric">
                    {formatQuantity(item.quantidade)}
                    {item.um ? ` ${item.um}` : ""}
                  </td>
                  <td className="sm-table__col--numeric">{formatCurrencyBrl(item.valor)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 ? (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={onPageChange}
        />
      ) : null}
    </section>
  );
}
