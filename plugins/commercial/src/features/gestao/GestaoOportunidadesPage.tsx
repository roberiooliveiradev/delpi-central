import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../api/gestaoApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTextField,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigateGestaoOportunidadeDetail } from "../../app/pluginNavigation";
import { GESTAO_CONTENT } from "../../content/gestaoContent";
import type { CommercialProposal } from "../../types/gestao";
import { formatDisplayDate } from "../../utils/dates";
import { GestaoFilters } from "./components/GestaoFilters";
import { useGestaoFilters } from "./hooks/useGestaoFilters";
import { buildGestaoFilterSearchParams } from "./utils/gestaoFilterUrl";

type GestaoOportunidadesPageProps = {
  basePath: string;
};

export function GestaoOportunidadesPage({ basePath }: GestaoOportunidadesPageProps) {
  const filters = useGestaoFilters();
  const [items, setItems] = useState<CommercialProposal[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getCommercialProposals(
      {
        ...filters.apiParams,
        page: 1,
        page_size: 50,
        search: search.trim() || undefined,
        sort_by: "proposal_date",
        sort_dir: "desc",
      },
      controller.signal,
    )
      .then((page) => {
        if (controller.signal.aborted) return;
        setItems(page.items ?? []);
        setTotal(page.total ?? 0);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar oportunidades.");
        setItems([]);
        setTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
    search,
    reloadKey,
  ]);

  const columns: DataTableColumn<CommercialProposal>[] = [
    {
      key: "ov",
      header: "OV",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={() =>
            navigateGestaoOportunidadeDetail(row.proposal_number, {
              basePath,
              search: buildGestaoFilterSearchParams(filters.filterState),
            })
          }
        >
          {row.proposal_number}
        </button>
      ),
    },
    { key: "rev", header: "Rev.", render: (row) => row.revision || "—" },
    { key: "customer", header: "Cliente", render: (row) => row.customer_code || "—" },
    { key: "status", header: "Status", render: (row) => row.status_label || row.status_code || "—" },
    { key: "stage", header: "Etapa", render: (row) => row.stage || "—" },
    { key: "date", header: "Data", render: (row) => formatDisplayDate(row.proposal_date) },
  ];

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={GESTAO_CONTENT.oportunidades.title}
          hint={GESTAO_CONTENT.oportunidades.subtitle}
        />
        <ActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <GestaoFilters
        dateStart={filters.dateStart}
        dateEnd={filters.dateEnd}
        competence={filters.competence}
        branches={filters.branches}
        customerSegment={filters.customerSegment}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
      />

      <CommercialTextField
        label="Busca"
        value={search}
        onChange={setSearch}
        placeholder="Número da OV, cliente…"
      />

      <SectionCard
        title={`Oportunidades (${total.toLocaleString("pt-BR")})`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? <CommercialLoadingCard title="Carregando…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {!loading && !error ? (
          <DataTable
            rows={items}
            columns={columns}
            rowKey={(row) => `${row.branch}-${row.proposal_number}-${row.revision}`}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
