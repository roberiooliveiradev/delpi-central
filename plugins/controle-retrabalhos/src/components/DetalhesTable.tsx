import { useCallback, useMemo, useState } from "react";

import {
  DataTable,
  dataTableBemClasses,
  dataTableSectionBemClasses,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

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

const SECTION = dataTableSectionBemClasses("cr");
const TABLE = dataTableBemClasses("cr");

const TABLE_LABELS = {
  emptyMessage: "Nenhum registro nesta página.",
  loadingMessage: "Carregando…",
  sortByAriaLabel: (header: string) => `Ordenar por ${header}`,
  headerHelpAriaLabel: (header: string) => `Ajuda: ${header}`,
};

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

  const columns = useMemo<DataTableColumn<RetrabalhoDetalheItem>[]>(
    () => [
      {
        key: "data",
        header: "Data",
        render: (item) => formatDatePtBr(item.dataReferencia),
      },
      {
        key: "recurso",
        header: "Recurso",
        render: (item) => item.recurso || "—",
      },
      {
        key: "operador",
        header: "Operador",
        render: (item) => item.nomeOperador || "—",
      },
      {
        key: "horas",
        header: "Horas",
        render: (item) => formatHours(item.tempoHoras),
      },
      {
        key: "custo",
        header: "Custo",
        render: (item) => formatCurrencyBrl(item.valorParada),
      },
      {
        key: "motivo",
        header: "Motivo / obs.",
        render: (item) => joinMotivoObservacao(item.motivo, item.observacao),
      },
    ],
    [],
  );

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
    <section className={SECTION.section} aria-busy={loading}>
      <header className={SECTION.header}>
        <div>
          <h2 className={SECTION.title}>Detalhes dos apontamentos</h2>
          {data ? (
            <p className={SECTION.meta}>
              Página {data.page} de {data.totalPages} — {data.total.toLocaleString("pt-BR")}{" "}
              registro(s)
            </p>
          ) : null}
        </div>
        <div className={SECTION.actions}>
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
        <DataTable
          columns={columns}
          rows={items}
          rowKey={(item) => `${item.recno}-${item.dataReferencia}`}
          classNames={TABLE}
          labels={TABLE_LABELS}
          layout="section"
        />
      )}

      {data ? (
        <Pagination
          page={page}
          pageSize={data.pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={onPageChange}
          footerClassName={SECTION.footer}
        />
      ) : null}
    </section>
  );
}
