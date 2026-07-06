import { useCallback, useState } from "react";

import { fetchAllRetrabalhoDetalhes } from "../api/fetchAllRetrabalhoDetalhes";
import type { RetrabalhoDetalheItem, RetrabalhoDetalhesData, RetrabalhoQueryFilters } from "../types/retrabalho";
import { exportDetalhesExcel } from "../utils/exportDetalhes";
import {
  formatCurrencyBrl,
  formatDatePtBr,
  formatHours,
  joinMotivoObservacao,
} from "../utils/formatters";
import { ExportExcelButton } from "./ExportExcelButton";

type DetalhesTableProps = {
  data: RetrabalhoDetalhesData | null;
  filters: RetrabalhoQueryFilters;
  loading?: boolean;
  onPageChange: (page: number) => void;
  onExportError?: (message: string) => void;
};

export function DetalhesTable({
  data,
  filters,
  loading = false,
  onPageChange,
  onExportError,
}: DetalhesTableProps) {
  const [exporting, setExporting] = useState(false);
  const items: RetrabalhoDetalheItem[] = data?.items ?? [];
  const page = data?.page ?? 1;
  const totalPages = data?.totalPages ?? 1;
  const total = data?.total ?? 0;

  const handleExportExcel = useCallback(async () => {
    if (exporting || total <= 0) return;

    setExporting(true);
    try {
      const allItems = await fetchAllRetrabalhoDetalhes(filters);
      await exportDetalhesExcel(allItems, filters);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Não foi possível exportar o Excel.";
      onExportError?.(message);
    } finally {
      setExporting(false);
    }
  }, [exporting, filters, onExportError, total]);

  return (
    <section className="cr-card cr-table-card">
      <header className="cr-table-card__header">
        <div>
          <h2>Detalhes dos apontamentos</h2>
          {data ? (
            <p>
              Página {data.page} de {data.totalPages} — {data.total.toLocaleString("pt-BR")} registro(s)
            </p>
          ) : null}
        </div>
        <div className="cr-table-card__actions">
          <ExportExcelButton
            disabled={loading || total <= 0}
            exporting={exporting}
            onExport={handleExportExcel}
          />
        </div>
      </header>

      <div className="cr-table-wrap">
        <table className="cr-table">
          <thead>
            <tr>
              <th>Data</th>
              <th>Recurso</th>
              <th>Operador</th>
              <th>Horas</th>
              <th>Custo</th>
              <th>Motivo / obs.</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="cr-table__loading">
                  Carregando detalhes…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="cr-table__empty">
                  Nenhum registro nesta página.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={`${item.recno}-${item.dataReferencia}`}>
                  <td>{formatDatePtBr(item.dataReferencia)}</td>
                  <td>{item.recurso || "—"}</td>
                  <td>{item.nomeOperador || "—"}</td>
                  <td>{formatHours(item.tempoHoras)}</td>
                  <td>{formatCurrencyBrl(item.valorParada)}</td>
                  <td>{joinMotivoObservacao(item.motivo, item.observacao)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <footer className="cr-table-card__footer">
        <button
          type="button"
          className="cr-btn cr-btn--secondary"
          disabled={loading || page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Anterior
        </button>
        <span>
          Página {page} / {totalPages}
        </span>
        <button
          type="button"
          className="cr-btn cr-btn--secondary"
          disabled={loading || page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Próxima
        </button>
      </footer>
    </section>
  );
}
