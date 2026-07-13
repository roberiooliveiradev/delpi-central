import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { HistoricoDetailModal } from "../components/HistoricoDetailModal";
import { HistoricoFiltersBar } from "../components/HistoricoFilters";
import { HistoricoTable } from "../components/HistoricoTable";
import { PageShell } from "../components/PageShell";
import { Pagination } from "../components/Pagination";
import { branchLabel } from "../constants/branch";
import { useInspecoesProcessoHistorico } from "../hooks/useInspecoesProcessoHistorico";
import type { InspecoesProcessoHistoricoItem } from "../types/api";

type HistoricoPageProps = {
  branch: string;
  active?: boolean;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
};

export function HistoricoPage({
  branch,
  active = true,
  refreshToken = 0,
  onLoadingChange,
}: HistoricoPageProps) {
  const {
    draftFilters,
    updateDraftFilters,
    clearFilters,
    search,
    page,
    pageSize,
    setPage,
    setPageSize,
    pageSizeOptions,
    items,
    hasNext,
    hasSearched,
    loading,
    prefetching,
    error,
    reload,
  } = useInspecoesProcessoHistorico(branch, refreshToken);

  const [selectedOrdemProducao, setSelectedOrdemProducao] = useState<string | null>(null);
  const [trackedBranch, setTrackedBranch] = useState(branch);
  if (branch !== trackedBranch) {
    setTrackedBranch(branch);
    setSelectedOrdemProducao(null);
  }

  useEffect(() => {
    if (!active) return;
    onLoadingChange?.(loading);
  }, [active, loading, onLoadingChange]);

  const handleViewDetail = useCallback((item: InspecoesProcessoHistoricoItem) => {
    const ordem = item.ordem_producao?.trim();
    if (!ordem) return;
    setSelectedOrdemProducao(ordem);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedOrdemProducao(null);
  }, []);

  return (
    <PageShell
      title="Histórico"
      description={`Listagem paginada de ordens de produção para ${branchLabel(branch)} · últimos 12 meses.`}
    >
      <HistoricoFiltersBar
        filters={draftFilters}
        loading={loading}
        onChange={updateDraftFilters}
        onSearch={search}
        onClear={clearFilters}
      />

      {loading && items.length === 0 ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando histórico…</p>
        </div>
      ) : null}

      {prefetching && items.length > 0 ? (
        <div className="ip-alert ip-alert--info" role="status" aria-live="polite">
          <p>Carregando próximas páginas em segundo plano…</p>
        </div>
      ) : null}

      {error ? (
        <div className="ip-alert ip-alert--error" role="alert">
          <p>{error}</p>
          <button type="button" className="ip-button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!hasSearched && !loading && !error ? (
        <EmptyState
          title="Pronto para buscar"
          description="Informe ordem de produção ou código de produto e clique em Buscar. A consulta cobre os últimos 12 meses desta filial."
        />
      ) : null}

      {hasSearched && !loading && !error && items.length === 0 ? (
        <EmptyState
          title="Nenhuma OP encontrada"
          description="Não há registros para os filtros aplicados nesta filial nos últimos 12 meses."
        />
      ) : null}

      {hasSearched && !error && items.length > 0 ? (
        <section className="ip-panel" aria-label="Resultados do histórico">
          <HistoricoTable items={items} onViewDetail={handleViewDetail} />
          <Pagination
            page={page}
            pageSize={pageSize}
            pageSizeOptions={pageSizeOptions}
            hasNext={hasNext}
            loading={loading}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
          />
        </section>
      ) : null}

      <p className="ip-muted-note">
        Histórico paginado por OP (25 por página). Ao buscar, a primeira página aparece na
        hora e as seguintes são pré-carregadas. Trocar de aba não refaz a consulta.
      </p>

      <HistoricoDetailModal
        branch={branch}
        ordemProducao={selectedOrdemProducao}
        onClose={handleCloseDetail}
      />
    </PageShell>
  );
}
