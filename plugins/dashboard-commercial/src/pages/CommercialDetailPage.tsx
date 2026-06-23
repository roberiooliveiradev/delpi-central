import { useMemo } from "react";
import {
  ArrowLeft,
  Building2,
  FileText,
  History,
  RefreshCw,
  UserRound,
} from "lucide-react";

import { CommercialProposalHistorySection } from "../components/CommercialProposalHistorySection";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { ProposalStatusBadge } from "../components/ProposalStatusBadge";
import { COMMERCIAL_ROUTES } from "../constants/routes";
import { useCommercialDetailRequestScope } from "../hooks/useCommercialDetailRequestScope";
import { useCommercialProposalDetail } from "../hooks/useCommercialProposalDetail";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { EMPTY_REQUEST_PROGRESS } from "../utils/loadingProgress";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { readCommercialFilters } from "../utils/filterUrl";
import { navigateCommercialBack } from "../utils/navigation";

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
            className="dc-secondary-btn"
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
          <p className="dc-detail-page__subtitle">
            {data.description ?? "Sem descrição"} · {periodLabel}
          </p>
        </div>
        <div className="dc-detail-page__actions">
          <button
            type="button"
            className="dc-secondary-btn"
            onClick={detail.reload}
          >
            <RefreshCw size={16} aria-hidden />
            Atualizar
          </button>
          <button
            type="button"
            className="dc-secondary-btn"
            onClick={handleBack}
          >
            <ArrowLeft size={16} aria-hidden />
            Voltar
          </button>
        </div>
      </header>

      <section className="dc-kpi-grid dc-detail-kpi-grid" aria-busy={detail.loading}>
        <KpiCard
          title="Status"
          value={data.status_label ?? data.status_code ?? "—"}
          contextLabel={`Estágio ${data.stage_label ?? data.stage ?? "—"}`}
          icon={<FileText size={22} />}
          loading={false}
        />
        <KpiCard
          title="Abertura"
          value={formatDisplayDate(data.proposal_date)}
          contextLabel="Data AD1_DATA"
          icon={<Building2 size={22} />}
          loading={false}
        />
        <KpiCard
          title="Fechamento"
          value={formatDisplayDate(data.end_date)}
          contextLabel="Data AD1_DTFIM"
          icon={<History size={22} />}
          loading={false}
        />
      </section>

      <div className="dc-detail-layout">
        <DetailCard title="Proposta" icon={<FileText size={20} />} hint="Cabeçalho AD1010">
          <DetailFieldGrid
            fields={[
              { label: "Filial", value: data.branch },
              { label: "Nº proposta", value: data.proposal_number },
              { label: "Revisão", value: data.revision },
              {
                label: "Descrição",
                value: data.description ?? "—",
                wide: true,
              },
              { label: "Processo", value: data.process_label ?? data.process_code ?? "—" },
              { label: "Estágio", value: data.stage_label ?? data.stage ?? "—" },
              { label: "Abertura", value: formatDisplayDate(data.proposal_date) },
              { label: "Fechamento", value: formatDisplayDate(data.end_date) },
              {
                label: "Status",
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
          icon={<UserRound size={20} />}
          hint="SA1010 / SA3010"
        >
          <DetailFieldGrid
            fields={[
              { label: "Cliente", value: data.customer_name ?? "—" },
              { label: "Código cliente", value: data.customer_code ?? "—" },
              { label: "Loja", value: data.customer_store ?? "—" },
              { label: "Vendedor", value: data.seller_name ?? "—" },
              { label: "Código vendedor", value: data.seller_code ?? "—" },
            ]}
          />
        </DetailCard>

        <DetailCard
          title="Histórico da OV"
          icon={<History size={20} />}
          hint="Eventos AIJ010 — processo e estágio"
          className="dc-detail-card--wide"
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
