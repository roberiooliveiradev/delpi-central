import { RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { listProposalsDocuments } from "../../api/commercialProposalsApi";
import {
  CommercialActionButton,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagination,
  CommercialSectionCard,
  CommercialSectionHintLabel,
  CommercialStateBanner,
  CommercialTextField,
} from "../../app/commercialUi";
import { PROPOSALS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type {
  ProposalDocumentListData,
  ProposalDocumentSortDirection,
  ProposalDocumentSortKey,
} from "../../types/proposalsDocument";
import { AnalyticsDeepPagePath } from "../analytics/components/AnalyticsDeepPagePath";
import { ProposalsDocumentsTable } from "./ProposalsDocumentsTable";

const PAGE_SIZE = 20;
const SEARCH_DEBOUNCE_MS = 350;

type ProposalsPageProps = {
  basePath: string;
};

export function ProposalsPage({ basePath }: ProposalsPageProps) {
  const [data, setData] = useState<ProposalDocumentListData | null>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<ProposalDocumentSortKey>("data");
  const [sortDirection, setSortDirection] = useState<ProposalDocumentSortDirection>("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(
      () => setDebouncedSearch(search.trim()),
      SEARCH_DEBOUNCE_MS,
    );
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void listProposalsDocuments(
      { search: debouncedSearch, page, pageSize: PAGE_SIZE, sortBy: sortKey, sortDir: sortDirection },
      controller.signal,
    )
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
  }, [debouncedSearch, page, sortKey, sortDirection, reloadKey]);

  const handleSortChange = (columnKey: string) => {
    const key = columnKey as ProposalDocumentSortKey;
    setSortDirection((current) => key === sortKey ? (current === "asc" ? "desc" : "asc") : "asc");
    setSortKey(key);
    setPage(1);
  };

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <section className="cm-page-stack">
      <AnalyticsDeepPagePath
        basePath={basePath}
        current={PROPOSALS_CONTENT.list.title}
        backTo="home"
        viewId="proposals"
      />
      <CommercialPageHero
        aria-label={PROPOSALS_CONTENT.list.title}
        title={
          <CommercialSectionHintLabel
            label={PROPOSALS_CONTENT.list.title}
            hint={CM_HELP.proposals.page}
          />
        }
        description={PROPOSALS_CONTENT.list.subtitle}
        actions={
          <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </CommercialActionButton>
        }
      />

      <CommercialStateBanner>{CM_HELP.proposals.scopeNote}</CommercialStateBanner>

      <CommercialTextField
        label="Busca"
        hint={CM_HELP.proposals.search}
        value={search}
        onChange={setSearch}
        placeholder="OV, proposta, cliente…"
      />

      <CommercialSectionCard
        title={`Propostas (${total.toLocaleString("pt-BR")})`}
        hint={CM_HELP.proposals.list}
      >
        {loading ? <CommercialLoadingCard title="Carregando propostas…" variant="panel" /> : null}
        {error ? <CommercialEmptyState message={error} role="alert" /> : null}
        {!loading && !error && items.length === 0 ? (
          <CommercialEmptyState
            title={PROPOSALS_CONTENT.list.empty}
            message={
              debouncedSearch
                ? PROPOSALS_CONTENT.list.emptySearch
                : PROPOSALS_CONTENT.list.empty
            }
          />
        ) : null}
        {!loading && !error && items.length > 0 ? (
          <>
            <ProposalsDocumentsTable
              rows={items}
              basePath={basePath}
              loading={loading}
              sortKey={sortKey}
              sortDirection={sortDirection}
              onSortChange={handleSortChange}
            />
            {total > PAGE_SIZE ? (
              <CommercialPagination
                page={page}
                pageSize={PAGE_SIZE}
                total={total}
                onPageChange={setPage}
              />
            ) : null}
          </>
        ) : null}
      </CommercialSectionCard>
    </section>
  );
}
