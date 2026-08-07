import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { ArrowLeft, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { getCommercialProposalByNumber } from "../../api/gestaoApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { GESTAO_CONTENT } from "../../content/gestaoContent";
import type { CommercialProduct, CommercialProposalDetail, CommercialProposalHistoryEvent } from "../../types/gestao";
import { formatDisplayDate } from "../../utils/dates";
import { useGestaoFilters } from "./hooks/useGestaoFilters";
import { buildGestaoFilterSearchParams } from "./utils/gestaoFilterUrl";
import { resolveGestaoApiBranch } from "./utils/gestaoBranchFilters";

type GestaoOportunidadeDetailPageProps = {
  basePath: string;
  proposalNumber: string;
  search?: string;
};

function readQueryParam(search: string | undefined, key: string): string {
  if (typeof window === "undefined" && !search) return "";
  const params = new URLSearchParams(search ?? window.location.search);
  return (params.get(key) ?? "").trim();
}

export function GestaoOportunidadeDetailPage({
  basePath,
  proposalNumber,
  search,
}: GestaoOportunidadeDetailPageProps) {
  const filters = useGestaoFilters();
  const branchFromUrl = readQueryParam(search, "branch");
  const revisionFromUrl = readQueryParam(search, "revision");
  const branch =
    branchFromUrl ||
    resolveGestaoApiBranch(filters.branches) ||
    "01";

  const [data, setData] = useState<CommercialProposalDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getCommercialProposalByNumber(
      proposalNumber,
      { branch, revision: revisionFromUrl || undefined },
      controller.signal,
    )
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar OV.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [proposalNumber, branch, revisionFromUrl, reloadKey]);

  const productColumns: DataTableColumn<CommercialProduct>[] = useMemo(
    () => [
      { key: "code", header: "Código", render: (row) => row.code },
      { key: "desc", header: "Descrição", render: (row) => row.description || "—" },
      {
        key: "qty",
        header: "Qtd",
        render: (row) => (row.qtd_pi != null ? String(row.qtd_pi) : "—"),
      },
    ],
    [],
  );

  const historyColumns: DataTableColumn<CommercialProposalHistoryEvent>[] = useMemo(
    () => [
      { key: "rev", header: "Rev.", render: (row) => row.revision },
      { key: "process", header: "Processo", render: (row) => row.process_label || row.process_code },
      { key: "stage", header: "Etapa", render: (row) => row.stage_label || row.stage_code },
      { key: "start", header: "Início", render: (row) => formatDisplayDate(row.start_date) },
      { key: "end", header: "Fim", render: (row) => formatDisplayDate(row.end_date) },
      { key: "dur", header: "Duração", render: (row) => row.duration_display || "—" },
    ],
    [],
  );

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={`OV ${proposalNumber}`}
          hint={GESTAO_CONTENT.oportunidades.detail}
        />
        <div className="cm-nav-row">
          <ActionButton
            variant="ghost"
            onClick={() =>
              navigatePluginView("gestao_oportunidades", {
                basePath,
                search: buildGestaoFilterSearchParams(filters.filterState),
              })
            }
          >
            <ArrowLeft size={16} aria-hidden="true" /> Voltar
          </ActionButton>
          <ActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </ActionButton>
        </div>
      </header>

      {loading ? <CommercialLoadingCard title="Carregando OV…" variant="panel" /> : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loading && data ? (
        <>
          <SectionCard
            title="Cabeçalho"
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialDetailFieldGrid
              fields={[
                { label: "OV", value: data.proposal_number },
                { label: "Revisão", value: data.revision },
                { label: "Filial", value: data.branch },
                { label: "Status", value: data.status_label || data.status_code || "—" },
                { label: "Cliente", value: data.customer_name || data.customer_code || "—" },
                { label: "Vendedor", value: data.seller_name || data.seller_code || "—" },
                { label: "Data", value: formatDisplayDate(data.proposal_date) },
                { label: "Etapa", value: data.stage_label || data.stage || "—" },
                { label: "Processo", value: data.process_label || data.process_code || "—" },
                { label: "Descrição", value: data.description || "—" },
              ]}
            />
          </SectionCard>

          <SectionCard
            title="Produtos"
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <DataTable
              rows={data.list_products ?? []}
              columns={productColumns}
              rowKey={(row, index) => `${row.code}-${index}`}
              classNames={cmDataTableClassNames}
              labels={cmDataTableLabels}
              layout="section"
            />
          </SectionCard>

          <SectionCard
            title="Histórico"
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <DataTable
              rows={data.list_history ?? []}
              columns={historyColumns}
              rowKey={(row, index) => `${row.revision}-${row.process_code}-${row.stage_code}-${index}`}
              classNames={cmDataTableClassNames}
              labels={cmDataTableLabels}
              layout="section"
            />
          </SectionCard>
        </>
      ) : null}
    </section>
  );
}
