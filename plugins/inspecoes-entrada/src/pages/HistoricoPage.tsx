import { IE_STATE_BOX } from "../ui/stateChrome";
import { useEffect, useState } from "react";

import { branchFromPathname } from "../constants/branch";
import { HistoricoDetailModal } from "../components/HistoricoDetailModal";
import { HistoricoFilterBar } from "../components/HistoricoFilterBar";
import { HistoricoTable } from "../components/HistoricoTable";
import { Pagination } from "../components/Pagination";
import { useInspecoesEntradaHistorico } from "../hooks/useInspecoesEntradaHistorico";

type HistoricoPageProps = {
  pathname?: string;
  embedded?: boolean;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
};

export function HistoricoPage({
  pathname,
  embedded = false,
  refreshToken = 0,
  onLoadingChange,
}: HistoricoPageProps) {
  const routeBranch = branchFromPathname(pathname);
  const {
    branch,
    setBranch,
    filters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions,
    data,
    loading,
    error,
    reload,
  } = useInspecoesEntradaHistorico(routeBranch, refreshToken);

  const [selectedInspectionId, setSelectedInspectionId] = useState<string | null>(null);

  useEffect(() => {
    onLoadingChange?.(loading);
  }, [onLoadingChange, loading]);

  const total = data?.pagination.total ?? 0;
  const totalPages = data?.pagination.total_pages ?? 1;
  const items = data?.items ?? [];
  const showInitialLoading = loading && !data;
  const showEmpty = !loading && !error && total === 0;
  const branchLocked = routeBranch !== null;

  if (!embedded && pathname && !routeBranch) {
    return (
      <div className="dashboard-inspecoes-entrada dashboard-page">
        <div className="ie-app-shell">
          <div className="ie-alert ie-alert--error" role="alert">
            <p>
              Rota inválida. Use /apps/inspecoes-entrada/filial-01 ou
              /apps/inspecoes-entrada/filial-02.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const content = (
    <>
      <HistoricoFilterBar
        branch={branch}
        branchLocked={branchLocked}
        filters={filters}
        hasActiveFilters={hasActiveFilters}
        loading={loading}
        onBranchChange={setBranch}
        onChange={updateFilters}
        onClear={clearFilters}
      />

      {showInitialLoading ? (
        <div className={IE_STATE_BOX} role="status">
          Carregando histórico de inspeções…
        </div>
      ) : null}

      {!loading && error ? (
        <div className="ie-alert ie-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="ie-btn ie-btn--ghost" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {showEmpty ? (
        <div className={IE_STATE_BOX}>
          Nenhuma inspeção encontrada para os filtros selecionados.
        </div>
      ) : null}

      {!error && total > 0 ? (
        <section className="ie-card ie-table-card" aria-label="Histórico de inspeções">
          {loading ? (
            <div className="ie-table-loading" role="status">
              Atualizando resultados…
            </div>
          ) : null}
          <HistoricoTable
            items={items}
            onViewDetails={(item) => setSelectedInspectionId(item.inspection_id)}
          />
          <div className="ie-table-card__footer">
            <Pagination
              page={page}
              pageSize={pageSize}
              total={total}
              totalPages={totalPages}
              pageSizeOptions={pageSizeOptions}
              onPageChange={setPage}
              onPageSizeChange={setPageSize}
            />
          </div>
        </section>
      ) : null}

      <HistoricoDetailModal
        branch={branch}
        inspectionId={selectedInspectionId}
        onClose={() => setSelectedInspectionId(null)}
      />
    </>
  );

  if (embedded) {
    return content;
  }

  return (
    <div className="dashboard-inspecoes-entrada dashboard-page">
      <div className="ie-app-shell">{content}</div>
    </div>
  );
}
