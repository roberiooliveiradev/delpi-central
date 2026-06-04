import type { AdminInteractivitySummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";

type AdminInteractivityMetricsProps = {
  summary: AdminInteractivitySummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatPercent(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}

export function AdminInteractivityMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminInteractivityMetricsProps) {
  const topShown =
    summary?.topShown?.map((item) => ({
      label: item.label,
      value: formatNumber(item.count),
      key: item.label,
    })) ?? [];

  const topClicked =
    summary?.topClicked?.map((item) => ({
      label: item.label,
      value: formatNumber(item.count),
      key: item.label,
    })) ?? [];

  const showRankings = topShown.length > 0 || topClicked.length > 0;

  return (
    <AdminMetricSection
      id="mdc-admin-interactivity-metrics-title"
      domain="Qualidade"
      title="Interatividade (chips)"
      description={`Impressões em auditoria (interactivityMetrics) e cliques (chat.interactivity.clicked) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de interatividade..."
      isEmpty={!isLoading && !summary}
      emptyMessage="Não foi possível carregar o resumo de interatividade."
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Respostas com chips"
              value={formatNumber(summary.responsesWithChips)}
              hint="Turnos com bloco consolidado de sugestões."
            />
            <AdminKpiCard
              title="Chips exibidos"
              value={formatNumber(summary.suggestionsShownTotal)}
              hint="Total de sugestões mostradas (primários + overflow)."
            />
            <AdminKpiCard
              title="Cliques"
              value={formatNumber(summary.clicksCount)}
              hint="Chips acionados pelo usuário."
            />
            <AdminKpiCard
              title="CTR geral"
              value={formatPercent(summary.clickThroughRate)}
              hint="Cliques ÷ impressões de chip."
            />
            <AdminKpiCard
              title="«Mais opções»"
              value={formatNumber(summary.moreOptionsResponses)}
              hint="Respostas que exibiram overflow agrupado."
            />
          </AdminKpiGrid>

          {showRankings ? (
            <div className="mdc-admin-metric-section__grid-2">
              <article className="mdc-admin-kpi-card">
                <AdminRankedList title="Mais exibidos" items={topShown} />
              </article>
              {topClicked.length > 0 ? (
                <article className="mdc-admin-kpi-card">
                  <AdminRankedList title="Mais clicados" items={topClicked} />
                </article>
              ) : (
                <article className="mdc-admin-kpi-card">
                  <h3>Mais clicados</h3>
                  <p className="mdc-chat-muted">Sem cliques na janela.</p>
                </article>
              )}
            </div>
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
