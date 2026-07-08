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
import { LoadingActivityCard } from "./LoadingActivityCard";
import { Pagination } from "./Pagination";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../utils/loadingProgress";

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
  const showInitialLoading = loading && data === null;
  const showRefreshLoading = loading && data !== null;
  const initialFetchProgress = useTrackedSingleFetchProgress(showInitialLoading);
  const refreshFetchProgress = useTrackedSingleFetchProgress(showRefreshLoading);
  const initialLoadingProgress = useLoadingProgress(showInitialLoading, initialFetchProgress);
  const refreshLoadingProgress = useLoadingProgress(showRefreshLoading, refreshFetchProgress);

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
    <section className="cr-card cr-table-card" aria-busy={loading}>
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

      {showRefreshLoading ? (
        <LoadingActivityCard
          title="Atualizando detalhes"
          description="Carregando a página selecionada dos apontamentos de retrabalho."
          variant="compact"
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {showInitialLoading ? (
        <LoadingActivityCard
          title="Carregando detalhes dos apontamentos"
          description="Consultando registros paginados no TOTVS."
          progressPercent={initialLoadingProgress}
        />
      ) : (
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
            {items.length === 0 ? (
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
      )}

      {data ? (
        <Pagination
          page={page}
          pageSize={data.pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={onPageChange}
        />
      ) : null}
    </section>
  );
}
