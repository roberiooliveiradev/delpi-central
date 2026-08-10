import {
  ActionButton,
  DataTable,
  EmptyState,
  SectionCard,
  SegmentToggle,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { CalendarCheck, CalendarPlus, Flag, RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  getCommercialProposalByNumber,
  getCommercialProposalHistoryEvents,
} from "../../api/analyticsApi";
import { fetchOptional, fetchProductStructure } from "../../api/productionExtrasApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialActivityTimeline,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  CommercialPagePath,
  CommercialTitleWithHelp,
  UI_PREFIX,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { KpiCard } from "../../components/KpiCard";
import { ProductStructureTree } from "../../components/ProductStructureTree";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type {
  CommercialProduct,
  CommercialProposalDetail,
  CommercialProposalHistoryEvent,
} from "../../types/analytics";
import type { ProductStructureData } from "../../types/productionExtras";
import { formatDisplayDate } from "../../utils/dates";
import { formatQuantity } from "../../utils/format";
import {
  hasRenderableProductStructure,
  structureRoots,
} from "../../utils/productStructurePresentation";
import {
  formatProcessStageLabel,
  historyEventKey,
  mapProposalHistoryToTimelineItems,
  resolveHistoryDuration,
  resolveHistoryStatus,
} from "../../utils/proposalHistoryFormatting";
import { useAnalyticsFilters } from "./hooks/useAnalyticsFilters";
import { buildAnalyticsOpportunityBackSearch } from "./utils/analyticsFilterUrl";
import { resolveAnalyticsApiBranch } from "./utils/analyticsBranchFilters";

type AnalyticsOpportunityDetailPageProps = {
  basePath: string;
  proposalNumber: string;
  search?: string;
};

type HistoryView = "timeline" | "table";

function readQueryParam(search: string | undefined, key: string): string {
  if (typeof window === "undefined" && !search) return "";
  const params = new URLSearchParams(search ?? window.location.search);
  return (params.get(key) ?? "").trim();
}

export function AnalyticsOpportunityDetailPage({
  basePath,
  proposalNumber,
  search,
}: AnalyticsOpportunityDetailPageProps) {
  const filters = useAnalyticsFilters();
  const branchFromUrl = readQueryParam(search, "branch");
  const revisionFromUrl = readQueryParam(search, "revision");
  const branch =
    branchFromUrl ||
    resolveAnalyticsApiBranch(filters.branches) ||
    "01";

  const [data, setData] = useState<CommercialProposalDetail | null>(null);
  const [history, setHistory] = useState<CommercialProposalHistoryEvent[]>([]);
  const [structures, setStructures] = useState<
    { code: string; description?: string | null; structure: ProductStructureData }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [historyView, setHistoryView] = useState<HistoryView>("timeline");
  const backHref = buildPluginPath(
    "analytics_opportunities",
    basePath,
    buildAnalyticsOpportunityBackSearch(search),
  );

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setHistoryError(null);

    void (async () => {
      try {
        const [detailResult, historyResult] = await Promise.all([
          getCommercialProposalByNumber(
            proposalNumber,
            { branch, revision: revisionFromUrl || undefined },
            controller.signal,
          ),
          fetchOptional(() =>
            getCommercialProposalHistoryEvents(
              proposalNumber,
              {
                branch,
                revision: revisionFromUrl || undefined,
                start_date: filters.dateStart || undefined,
                end_date: filters.dateEnd || undefined,
              },
              controller.signal,
            ),
          ),
        ]);

        if (controller.signal.aborted) return;

        setData(detailResult);
        setHistory(historyResult.data?.items ?? []);
        if (historyResult.error) setHistoryError(historyResult.error);

        const products = detailResult.list_products ?? [];
        const seen = new Set<string>();
        const unique = products.filter((product) => {
          const code = product.code?.trim();
          if (!code || seen.has(code)) return false;
          seen.add(code);
          return true;
        });

        const structureResults = await Promise.all(
          unique.map(async (product) => {
            const result = await fetchOptional(() =>
              fetchProductStructure(product.code.trim(), controller.signal),
            );
            return {
              product,
              structure: result.data,
            };
          }),
        );

        if (controller.signal.aborted) return;

        setStructures(
          structureResults.flatMap(({ product, structure }) => {
            if (!structure || !hasRenderableProductStructure(structure)) return [];
            return [
              {
                code: product.code.trim(),
                description: product.description,
                structure,
              },
            ];
          }),
        );
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar OV.");
        setData(null);
        setHistory([]);
        setStructures([]);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    })();

    return () => controller.abort();
  }, [
    proposalNumber,
    branch,
    revisionFromUrl,
    reloadKey,
    filters.dateStart,
    filters.dateEnd,
  ]);

  const productColumns: DataTableColumn<CommercialProduct>[] = useMemo(
    () => [
      { key: "code", header: "Código", render: (row) => row.code },
      {
        key: "desc",
        header: "Descrição",
        render: (row) => row.description || "—",
      },
      {
        key: "group",
        header: "Grupo",
        render: (row) => row.group_code || "—",
      },
      {
        key: "type",
        header: "Tipo",
        render: (row) =>
          row.type ? (
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              label={row.type}
              variant={row.type === "PA" ? "success" : "info"}
            />
          ) : (
            "—"
          ),
      },
      {
        key: "qty",
        header: "Qtd PI",
        align: "right",
        render: (row) => (row.qtd_pi != null ? formatQuantity(row.qtd_pi) : "—"),
      },
    ],
    [],
  );

  const historyColumns: DataTableColumn<CommercialProposalHistoryEvent>[] = useMemo(
    () => [
      { key: "rev", header: "Rev.", render: (row) => row.revision },
      {
        key: "process",
        header: "Processo",
        render: (row) => formatProcessStageLabel(row.process_code, row.process_label),
      },
      {
        key: "stage",
        header: "Etapa",
        render: (row) => formatProcessStageLabel(row.stage_code, row.stage_label),
      },
      {
        key: "start",
        header: "Início",
        render: (row) => formatDisplayDate(row.start_date),
      },
      {
        key: "end",
        header: "Fim",
        render: (row) => formatDisplayDate(row.end_date),
      },
      {
        key: "dur",
        header: "Duração",
        render: (row) => resolveHistoryDuration(row),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => resolveHistoryStatus(row),
      },
    ],
    [],
  );

  const timelineItems = useMemo(
    () => mapProposalHistoryToTimelineItems(history),
    [history],
  );

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Oportunidades",
          href: backHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(backHref);
          },
        }}
        current={`OV ${proposalNumber}`}
      />
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={`OV ${proposalNumber}`}
          hint={ANALYTICS_CONTENT.oportunidades.detail}
        />
        <div className="cm-nav-row">
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
          <div className="cm-ov-kpi-row">
            <KpiCard
              title="Status"
              titleHint={CM_HELP.analytics.ovStatus}
              value={data.status_label || data.status_code || "—"}
              icon={<Flag size={22} aria-hidden="true" />}
            />
            <KpiCard
              title="Abertura"
              titleHint={CM_HELP.analytics.ovOpen}
              value={formatDisplayDate(data.proposal_date)}
              icon={<CalendarPlus size={22} aria-hidden="true" />}
            />
            <KpiCard
              title="Fechamento"
              titleHint={CM_HELP.analytics.ovClose}
              value={formatDisplayDate(data.end_date)}
              icon={<CalendarCheck size={22} aria-hidden="true" />}
            />
          </div>

          <div className="cm-ov-detail-grid">
            <SectionCard
              title="Proposta"
              hint={CM_HELP.analytics.ovHeader}
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              <CommercialDetailFieldGrid
                fields={[
                  { label: "OV", value: data.proposal_number },
                  { label: "Revisão", value: data.revision },
                  { label: "Filial", value: data.branch },
                  {
                    label: "Status",
                    value: (
                      <StatusBadge
                        classNames={cmStatusBadgeClassNames}
                        label={data.status_label || data.status_code || "—"}
                        variant="info"
                      />
                    ),
                  },
                  {
                    label: "Processo",
                    value: formatProcessStageLabel(data.process_code, data.process_label),
                  },
                  {
                    label: "Estágio",
                    value: formatProcessStageLabel(data.stage, data.stage_label),
                  },
                  { label: "Abertura", value: formatDisplayDate(data.proposal_date) },
                  { label: "Fechamento", value: formatDisplayDate(data.end_date) },
                  { label: "Descrição", value: data.description || "—" },
                ]}
              />
            </SectionCard>

            <SectionCard
              title="Cliente e vendedor"
              hint={CM_HELP.analytics.ovCustomer}
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Cliente", value: data.customer_name || "—" },
                  { label: "Código", value: data.customer_code || "—" },
                  { label: "Loja", value: data.customer_store || "—" },
                  { label: "Vendedor", value: data.seller_name || "—" },
                  { label: "Cód. vendedor", value: data.seller_code || "—" },
                ]}
              />
            </SectionCard>
          </div>

          <SectionCard
            title="Produtos"
            hint={CM_HELP.analytics.ovProducts}
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

          {structures.length > 0 ? (
            <SectionCard
              title="Estrutura do produto"
              hint={CM_HELP.analytics.ovBom}
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              {structures.map((entry) => (
                <div key={entry.code} className="cm-open-orders-detail__op-card">
                  <ProductStructureTree
                    nodes={structureRoots(entry.structure)}
                    caption={`${entry.code}${entry.description ? ` — ${entry.description}` : ""}`}
                    expandDepth={1}
                  />
                </div>
              ))}
            </SectionCard>
          ) : null}

          <SectionCard
            title="Histórico da OV"
            hint={CM_HELP.analytics.ovHistory}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <div className="cm-ov-history-toggle">
              <SegmentToggle
                prefix={UI_PREFIX}
                size="sm"
                ariaLabel="Modo do histórico"
                idPrefix="ov-history-view"
                value={historyView}
                onChange={setHistoryView}
                options={[
                  { value: "timeline", label: "Linha do tempo" },
                  { value: "table", label: "Tabela" },
                ]}
              />
            </div>
            {historyError ? <p role="alert">{historyError}</p> : null}
            {historyView === "timeline" ? (
              <CommercialActivityTimeline
                items={timelineItems}
                emptyMessage="Nenhum evento registrado no histórico da OV."
                aria-label="Linha do tempo da OV"
              />
            ) : (
              <DataTable
                rows={history}
                columns={historyColumns}
                rowKey={(row, index) => historyEventKey(row, index)}
                classNames={cmDataTableClassNames}
                labels={cmDataTableLabels}
                layout="section"
              />
            )}
          </SectionCard>
        </>
      ) : null}
    </section>
  );
}
