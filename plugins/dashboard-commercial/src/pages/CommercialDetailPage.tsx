import { useMemo } from "react";
import {
  ArrowLeft,
  Building2,
  FileText,
  History,
  RefreshCw,
  UserRound,
} from "lucide-react";

import { CommercialProductStructuresSection } from "../components/CommercialProductStructuresSection";
import { CommercialProposalHistorySection } from "../components/CommercialProposalHistorySection";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { HelpTooltip } from "../components/HelpTooltip";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { ProposalStatusBadge } from "../components/ProposalStatusBadge";
import { DataTable } from "../components/table";
import { COMMERCIAL_ROUTES } from "../constants/routes";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useCommercialDetailRequestScope } from "../hooks/useCommercialDetailRequestScope";
import { useCommercialProductStructures } from "../hooks/useCommercialProductStructures";
import { useCommercialProposalDetail } from "../hooks/useCommercialProposalDetail";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { EMPTY_REQUEST_PROGRESS } from "../utils/loadingProgress";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { readCommercialFilters } from "../utils/filterUrl";
import { navigateCommercialBack } from "../utils/navigation";
import { commercialProductColumns } from "../utils/commercialProductsPresentation";

type CommercialDetailPageProps = {
  proposalNumber: string;
  branch?: string;
  revision?: string;
};

export function CommercialDetailPage({
  proposalNumber,
  branch,
  revision,
}: CommercialDetailPageProps) {
  const requestScope = useCommercialDetailRequestScope(
    proposalNumber,
    branch,
    revision
  );
  const detail = useCommercialProposalDetail(proposalNumber, requestScope);
  const loadingProgress = useLoadingProgress(detail.loading, EMPTY_REQUEST_PROGRESS);
  const productStructures = useCommercialProductStructures(detail.data?.list_products);

  const periodLabel = useMemo(
    () => formatPeriodLabel(requestScope.dateStart, requestScope.dateEnd),
    [requestScope.dateEnd, requestScope.dateStart]
  );

  const handleBack = () => {
    const filters = readCommercialFilters();
    navigateCommercialBack(COMMERCIAL_ROUTES.home, filters);
  };

  if (detail.loading && !detail.data) {
    return (
      <div className="dashboard-commercial dashboard-page dc-detail-page">
        <LoadingActivityCard
          title="Carregando detalhe da proposta"
          description={`OV ${proposalNumber} · ${periodLabel}`}
          progressPercent={loadingProgress}
        />
      </div>
    );
  }

  if (detail.error || !detail.data) {
    return (
      <div className="dashboard-commercial dashboard-page dc-detail-page">
        <div className="dc-detail-page__header">
          <button
            type="button"
            className="dc-ghost-btn"
            onClick={handleBack}
          >
            <ArrowLeft size={16} aria-hidden />
            Voltar
          </button>
        </div>
        <div className="dc-state dc-state--error" role="alert">
          <p>{detail.error ?? "Proposta não encontrada."}</p>
          <button
            type="button"
            className="dc-primary-btn"
            onClick={detail.reload}
          >
            Tentar novamente
          </button>
        </div>
      </div>
    );
  }

  const data = detail.data;
  const historyItems = data.list_history ?? [];

  return (
    <div className="dashboard-commercial dashboard-page dc-detail-page">
      <header className="dc-detail-page__header">
        <div>
          <p className="dc-detail-page__eyebrow">Proposta comercial</p>
          <h1 className="dc-detail-page__title">
            OV {data.proposal_number}
            <span className="dc-detail-page__meta">
              Filial {data.branch} · Rev. {data.revision}
            </span>
          </h1>
          <p className="dc-detail-page__subtitle dc-page-subtitle--with-help">
            {data.description ?? "Sem descrição"} · {periodLabel}
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.detail.pageSubtitle}
              ariaLabel="Ajuda: detalhe da proposta"
              className="dc-page-subtitle__help"
            />
          </p>
        </div>
        <div className="dc-header-actions dc-no-print">
          <div className="dc-header-action">
            <button
              type="button"
              className="dc-ghost-btn"
              onClick={detail.reload}
              disabled={detail.loading}
            >
              <RefreshCw size={16} aria-hidden />
              {detail.loading ? "Atualizando…" : "Atualizar"}
            </button>
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.actions.detailRefresh}
              ariaLabel="Ajuda: atualizar detalhe"
              className="dc-header-action__help"
            />
          </div>
          <div className="dc-header-action">
            <button
              type="button"
              className="dc-ghost-btn"
              onClick={handleBack}
            >
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
            <HelpTooltip
              content={COMMERCIAL_HELP_TOOLTIPS.actions.back}
              ariaLabel="Ajuda: voltar ao dashboard"
              className="dc-header-action__help"
            />
          </div>
        </div>
      </header>

      <section className="dc-kpi-grid dc-detail-kpi-grid" aria-busy={detail.loading}>
        <KpiCard
          title="Status"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.statusKpi}
          value={data.status_label ?? data.status_code ?? "—"}
          contextLabel={`Estágio ${data.stage_label ?? data.stage ?? "—"}`}
          icon={<FileText size={22} />}
          loading={false}
        />
        <KpiCard
          title="Abertura"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.openingKpi}
          value={formatDisplayDate(data.proposal_date)}
          contextLabel="Data AD1_DATA"
          icon={<Building2 size={22} />}
          loading={false}
        />
        <KpiCard
          title="Fechamento"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.closingKpi}
          value={formatDisplayDate(data.end_date)}
          contextLabel="Data de aceite (AD1_DTASSI)"
          icon={<History size={22} />}
          loading={false}
        />
      </section>

      <div className="dc-detail-layout">
        <DetailCard
          title="Proposta"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.proposalSection}
          icon={<FileText size={20} />}
          hint="Cabeçalho AD1010"
        >
          <DetailFieldGrid
            fields={[
              {
                label: "Filial",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalBranch,
                value: data.branch,
              },
              {
                label: "Nº proposta",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalNumber,
                value: data.proposal_number,
              },
              {
                label: "Revisão",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalRevision,
                value: data.revision,
              },
              {
                label: "Descrição",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalDescription,
                value: data.description ?? "—",
                wide: true,
              },
              {
                label: "Processo",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalProcess,
                value: data.process_label ?? data.process_code ?? "—",
              },
              {
                label: "Estágio",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalStage,
                value: data.stage_label ?? data.stage ?? "—",
              },
              {
                label: "Abertura",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalOpening,
                value: formatDisplayDate(data.proposal_date),
              },
              {
                label: "Fechamento",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalClosing,
                value: formatDisplayDate(data.end_date),
              },
              {
                label: "Status",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.proposalStatus,
                value: (
                  <ProposalStatusBadge
                    label={data.status_label ?? data.status_code ?? "—"}
                    category={data.status_category}
                    code={data.status_code}
                  />
                ),
              },
            ]}
          />
        </DetailCard>

        <DetailCard
          title="Cliente e vendedor"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.customerSection}
          icon={<UserRound size={20} />}
          hint="SA1010 / SA3010"
        >
          <DetailFieldGrid
            fields={[
              {
                label: "Cliente",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.customerName,
                value: data.customer_name ?? "—",
              },
              {
                label: "Código cliente",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.customerCode,
                value: data.customer_code ?? "—",
              },
              {
                label: "Loja",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.customerStore,
                value: data.customer_store ?? "—",
              },
              {
                label: "Vendedor",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.sellerName,
                value: data.seller_name ?? "—",
              },
              {
                label: "Código vendedor",
                hint: COMMERCIAL_HELP_TOOLTIPS.detail.sellerCode,
                value: data.seller_code ?? "—",
              },
            ]}
          />
        </DetailCard>

        <DetailCard
          title="Produtos"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.productsSection}
          hint={`${data.list_products?.length ?? 0} item(ns) vinculado(s)`}
          icon={<Building2 size={20} aria-hidden />}
          className="dc-detail-card--full"
        >
          <DataTable
            columns={commercialProductColumns}
            rows={data.list_products ?? []}
            rowKey={(row) => row.code || row.description || "product"}
            emptyMessage="Nenhum produto vinculado."
          />
        </DetailCard>

        {productStructures.shouldRender ? (
          <CommercialProductStructuresSection
            entries={productStructures.entries}
            loading={productStructures.loading}
          />
        ) : null}

        <DetailCard
          title="Histórico da OV"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.detail.historySection}
          icon={<History size={20} />}
          hint="Eventos AIJ010 — processo e estágio"
          className="dc-detail-card--full"
        >
          <CommercialProposalHistorySection
            items={historyItems}
            loading={detail.loading}
          />
        </DetailCard>
      </div>
    </div>
  );
}
