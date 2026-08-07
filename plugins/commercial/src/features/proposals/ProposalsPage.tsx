import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { listProposalsDocuments } from "../../api/commercialProposalsApi";
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
import { navigateProposalDetail } from "../../app/pluginNavigation";
import { PROPOSALS_CONTENT } from "../../content/analyticsContent";
import type { ProposalDocumentListData, ProposalDocumentListItem } from "../../types/proposalsDocument";

function filterProposalDocuments(
  items: ProposalDocumentListItem[],
  search: string,
): ProposalDocumentListItem[] {
  const query = search.trim().toLowerCase();
  if (!query) return items;
  const withoutOv = query.replace(/^ov\s*/i, "").trim();
  return items.filter((item) => {
    const haystack = [item.proposta_interna, item.numero_ov, item.oportunidade, item.cliente]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query) || (withoutOv !== query && haystack.includes(withoutOv));
  });
}

type ProposalsPageProps = {
  basePath: string;
};

export function ProposalsPage({ basePath }: ProposalsPageProps) {
  const [data, setData] = useState<ProposalDocumentListData | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void listProposalsDocuments(100, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Não foi possível carregar as propostas.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reloadKey]);

  const filtered = useMemo(
    () => filterProposalDocuments(data?.items ?? [], search),
    [data?.items, search],
  );

  const columns: DataTableColumn<ProposalDocumentListItem>[] = [
    {
      key: "ov",
      header: "Nº OV",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={() => navigateProposalDetail(row.proposta_interna, { basePath })}
        >
          {row.numero_ov || row.proposta_interna}
        </button>
      ),
    },
    { key: "interna", header: "Proposta", render: (row) => row.proposta_interna },
    { key: "cliente", header: "Cliente", render: (row) => row.cliente || "—" },
    { key: "oportunidade", header: "Oportunidade", render: (row) => row.oportunidade || "—" },
    { key: "versao", header: "Versão", render: (row) => row.versao || "—" },
    { key: "data", header: "Data", render: (row) => row.data || "—" },
    {
      key: "itens",
      header: "Itens",
      render: (row) => row.quantidade_itens.toLocaleString("pt-BR"),
    },
  ];

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={PROPOSALS_CONTENT.list.title}
          hint={PROPOSALS_CONTENT.list.subtitle}
        />
        <ActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <CommercialTextField
        label="Busca"
        hint={PROPOSALS_CONTENT.list.search}
        value={search}
        onChange={setSearch}
        placeholder="OV, proposta, cliente…"
      />

      <SectionCard
        title={`Propostas (${filtered.length.toLocaleString("pt-BR")})`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? <CommercialLoadingCard title="Carregando propostas…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {!loading && !error && filtered.length === 0 ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultTitle={PROPOSALS_CONTENT.list.empty}
            defaultMessage={
              search ? PROPOSALS_CONTENT.list.emptySearch : PROPOSALS_CONTENT.list.empty
            }
          />
        ) : null}
        {!loading && !error && filtered.length > 0 ? (
          <DataTable
            rows={filtered}
            columns={columns}
            rowKey={(row) => row.proposta_interna}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
