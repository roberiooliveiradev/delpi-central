import { GHOST_BTN } from "../ui/ghostChrome";
import { useMemo } from "react";
import { ArrowLeft, Lightbulb, RefreshCw, Wallet } from "lucide-react";

import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { KpiCard } from "../components/KpiCard";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { QualityNav } from "../components/QualityNav";
import { QUALITY_ROUTES } from "../constants/routes";
import { useKaizenDetail } from "../hooks/useKaizenDetail";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../hooks/useSimulatedLoadingProgress";
import { formatDisplayDate } from "../utils/dates";
import { readQualityFilters } from "../utils/filterUrl";
import { formatCurrency, formatDecimal } from "../utils/format";
import { navigateQualityBack } from "../utils/navigation";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type KaizenDetailPageProps = {
  kaizenId: string;
  pathname?: string;
};

export function KaizenDetailPage({ kaizenId, pathname }: KaizenDetailPageProps) {
  const { data, loading, error, reload } = useKaizenDetail(kaizenId);
  const initialFetchProgress = useTrackedSingleFetchProgress(loading);
  const initialLoadingProgress = useLoadingProgress(loading, initialFetchProgress);

  const identificationFields = useMemo(
    () =>
      data
        ? [
            { label: "Título", value: data.title, wide: true },
            { label: "Status", value: data.status ?? "—" },
            { label: "Setor", value: data.sector ?? "—" },
            { label: OPERATIONAL_UNIT_COLUMN_LABEL, value: formatOperationalUnitCode(data.branch) },
            {
              label: "Implementação",
              value: formatDisplayDate(data.date_implemented),
            },
            { label: "Responsável", value: data.accountable ?? "—" },
          ]
        : [],
    [data]
  );

  const savingsFields = useMemo(
    () =>
      data
        ? [
            {
              label: "Segundos por ocorrência",
              value: formatDecimal(data.seconds_per_occurrence),
            },
            {
              label: "Ocorrências por dia",
              value: formatDecimal(data.occurrences_per_day),
            },
            { label: "Custo hora", value: formatCurrency(data.hourly_cost) },
            {
              label: "Horas poupadas/dia",
              value: formatDecimal(data.hours_saved_per_day),
            },
            {
              label: "Economia/dia",
              value: formatCurrency(data.daily_savings),
            },
            {
              label: "Economia projetada/ano",
              value: formatCurrency(data.annual_savings),
            },
          ]
        : [],
    [data]
  );

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityNav currentPath={pathname ?? QUALITY_ROUTES.kaizen} />

      <header className="dq-page-header dq-detail-header">
        <div>
          <h1>{data?.title ?? "Detalhe do kaizen"}</h1>
          <p>
            {data
              ? [data.sector, data.branch, data.status].filter(Boolean).join(" · ")
              : "Carregando informações do kaizen"}
          </p>
        </div>
        <div className="dq-page-header__actions">
          <button
            type="button"
            className={`${GHOST_BTN} dq-no-print`}
            onClick={reload}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Atualizar
          </button>
          <button
            type="button"
            className={`${GHOST_BTN} dq-no-print`}
            onClick={() =>
              navigateQualityBack(QUALITY_ROUTES.kaizen, readQualityFilters())
            }
          >
            <ArrowLeft size={16} />
            Voltar
          </button>
        </div>
      </header>

      {error ? (
        <div className="dq-state dq-state--error" role="alert">
          <p>{error}</p>
          <button type="button" className={GHOST_BTN} onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {loading && !data ? (
        <LoadingActivityCard
          title="Carregando kaizen"
          description="Buscando os detalhes da melhoria selecionada."
          progressPercent={initialLoadingProgress}
        />
      ) : data ? (
        <>
          <section className="dq-kpi-grid dq-kpi-grid--detail" aria-busy={loading}>
            <KpiCard
              title="Investimento"
              value={formatCurrency(data.investment)}
              icon={<Wallet size={22} />}
              loading={loading && !data}
            />
            <KpiCard
              title="Economia/dia"
              value={formatCurrency(data.daily_savings)}
              icon={<Lightbulb size={22} />}
              loading={loading && !data}
            />
            <KpiCard
              title="Economia projetada/ano"
              value={formatCurrency(data.annual_savings)}
              subtitle="Economia diária × 365 dias"
              icon={<Wallet size={22} />}
              loading={loading && !data}
            />
          </section>

          <section className="dq-detail-layout">
            <article className="dq-card dq-detail-card">
              <h2 className="dq-section-title">Identificação</h2>
              <DetailFieldGrid fields={identificationFields} />
            </article>

            <article className="dq-card dq-detail-card">
              <h2 className="dq-section-title">Cálculo da economia</h2>
              <p className="dq-detail-card__hint">
                Economia diária = (segundos × ocorrências/dia ÷ 3600) × custo hora
              </p>
              <DetailFieldGrid fields={savingsFields} />
            </article>
          </section>
        </>
      ) : null}
    </div>
  );
}
