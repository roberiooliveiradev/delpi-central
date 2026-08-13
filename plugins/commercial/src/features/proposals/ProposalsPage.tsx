import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

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
  ProposalDocumentListItem,
} from "../../types/proposalsDocument";
import { AnalyticsDeepPagePath } from "../analytics/components/AnalyticsDeepPagePath";
import { ProposalsDocumentsTable } from "./ProposalsDocumentsTable";

const PAGE_SIZE = 20;

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
  const [page, setPage] = useState(1);
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

  useEffect(() => {
    setPage(1);
  }, [search]);

  const paged = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

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
        title={`Propostas (${filtered.length.toLocaleString("pt-BR")})`}
        hint={CM_HELP.proposals.list}
      >
        {loading ? <CommercialLoadingCard title="Carregando propostas…" variant="panel" /> : null}
        {error ? <CommercialEmptyState message={error} role="alert" /> : null}
        {!loading && !error && filtered.length === 0 ? (
          <CommercialEmptyState
            title={PROPOSALS_CONTENT.list.empty}
            message={
              search ? PROPOSALS_CONTENT.list.emptySearch : PROPOSALS_CONTENT.list.empty
            }
          />
        ) : null}
        {!loading && !error && filtered.length > 0 ? (
          <>
            <ProposalsDocumentsTable rows={paged} basePath={basePath} loading={loading} />
            {filtered.length > PAGE_SIZE ? (
              <CommercialPagination
                page={page}
                pageSize={PAGE_SIZE}
                total={filtered.length}
                onPageChange={setPage}
              />
            ) : null}
          </>
        ) : null}
      </CommercialSectionCard>
    </section>
  );
}
