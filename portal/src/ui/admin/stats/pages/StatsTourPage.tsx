// src/ui/admin/stats/pages/StatsTourPage.tsx

import { Compass, RefreshCw, Trophy } from "lucide-react";
import {
  StatsInsight,
  StatsInsightRow,
  StatsMiniKpi,
  StatsMiniKpiRow,
  formatPercent,
  statPercent,
} from "../StatsEnrichment";
import { formatGeneratedAt, StatsPageIntro } from "../StatsShared";
import {
  PORTAL_TOUR_STATUS_FILTERS,
  PORTAL_TOUR_STATUS_LABELS,
} from "../portalTourAdminLabels";
import { usePortalTourAdminMonitoring } from "../usePortalTourAdminMonitoring";
import { STATS_AUTO_REFRESH_MS } from "../statsTheme";

const PERIOD_OPTIONS = [
  { days: 7, label: "7 dias" },
  { days: 30, label: "30 dias" },
] as const;

export function StatsTourPage() {
  const {
    tourVersion,
    statusFilter,
    setStatusFilter,
    periodDays,
    setPeriodDays,
    page,
    setPage,
    pageSize,
    totalPages,
    canGoPrev,
    canGoNext,
    listData,
    topData,
    summary,
    loading,
    error,
    lastUpdatedAt,
    reload,
  } = usePortalTourAdminMonitoring();

  const items = listData?.items ?? [];
  const topItems = topData?.items ?? [];
  const total = summary?.total ?? 0;
  const exploring = summary?.exploring ?? 0;
  const completed = summary?.completed ?? 0;
  const activePct = statPercent(exploring + completed, total);
  const completionPct = statPercent(completed, total);

  return (
    <div className="admin-stats-page admin-stats-page--tour">
      <div className="admin-stats-page__head-row">
        <StatsPageIntro
          title="Acompanhamento do tour"
          description="Progresso gamificado do portal — quem está explorando, quem concluiu e ranking por desafios."
        />
        <div className="admin-stats-page__toolbar">
          <div className="admin-stats__generated-wrap">
            {lastUpdatedAt ? (
              <span className="admin-stats__generated">
                Atualizado: {formatGeneratedAt(lastUpdatedAt)}
              </span>
            ) : null}
            <span className="admin-stats__generated admin-stats__generated--muted">
              Atualização automática a cada {STATS_AUTO_REFRESH_MS / 1000}s
            </span>
          </div>
          <button
            type="button"
            className="admin-stats__refresh"
            onClick={() => void reload()}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "admin-stats__spin" : ""} />
            {loading ? "Atualizando…" : "Atualizar"}
          </button>
        </div>
      </div>

      <StatsMiniKpiRow>
        <StatsMiniKpi
          tone="primary"
          label="Explorando agora"
          value={exploring}
          hint={formatPercent(statPercent(exploring, total)) + " da base com tour"}
        />
        <StatsMiniKpi
          tone="success"
          label="Concluíram"
          value={completed}
          hint={formatPercent(completionPct) + " do total"}
        />
        <StatsMiniKpi
          label="Com registro"
          value={total}
          hint={`Versão ${tourVersion}`}
        />
        <StatsMiniKpi
          label="Ativos no tour"
          value={exploring + completed}
          hint={formatPercent(activePct) + " explorando ou concluído"}
        />
      </StatsMiniKpiRow>

      <StatsInsightRow>
        <StatsInsight
          label="Pularam (legado)"
          value={String(summary?.dismissed ?? 0)}
          detail="Registros antigos antes da remoção do botão Pular"
        />
        <StatsInsight
          label="Período do ranking"
          value={`${periodDays} dias`}
          detail="Desafios concluídos no intervalo"
        />
        <StatsInsight
          label="Top no período"
          value={String(topItems.length)}
          detail={
            topItems.length > 0
              ? `${topItems[0]?.name} lidera com ${topItems[0]?.questsInPeriod} desafios`
              : "Sem atividade recente"
          }
        />
      </StatsInsightRow>

      <div className="admin-stats-tour-grid">
        <section className="admin-stats__panel admin-stats-tour-ranking">
          <div className="admin-stats-panel__title-row">
            <h5>
              <Trophy size={14} aria-hidden="true" />
              Top exploradores
            </h5>
            <span className="admin-stats-panel__badge">{topItems.length}</span>
          </div>
          <p className="admin-stats-panel__lede">
            Ranking por desafios concluídos na versão atual do tour.
          </p>

          <div
            className="admin-stats-tour-period"
            role="tablist"
            aria-label="Período do ranking"
          >
            {PERIOD_OPTIONS.map((option) => (
              <button
                key={option.days}
                type="button"
                role="tab"
                aria-selected={periodDays === option.days}
                className={`admin-stats-tour-period__btn${
                  periodDays === option.days ? " is-active" : ""
                }`}
                onClick={() => setPeriodDays(option.days)}
              >
                {option.label}
              </button>
            ))}
          </div>

          {loading && !topItems.length ? (
            <p className="admin-stats__empty">Carregando ranking…</p>
          ) : error && !topItems.length ? (
            <p className="admin-stats__empty">{error}</p>
          ) : topItems.length === 0 ? (
            <p className="admin-stats__empty">
              Nenhum desafio concluído nos últimos {periodDays} dias.
            </p>
          ) : (
            <ol
              className="admin-stats-least-engaged-list admin-stats-top-explorers-list"
              aria-label="Top exploradores do tour do portal"
            >
              {topItems.map((item, index) => (
                <li key={item.userId} className="admin-stats-least-engaged-item">
                  <div className="admin-stats-least-engaged-item__head">
                    <div>
                      <strong>
                        #{index + 1} {item.name}
                      </strong>
                      <span className="admin-stats-least-engaged-item__email">
                        {item.email}
                      </span>
                    </div>
                    <div className="admin-stats-least-engaged-item__metrics">
                      <span>{item.questsInPeriod} desafios</span>
                    </div>
                  </div>
                  <div className="admin-stats-least-engaged-item__meta">
                    <span>
                      Última atividade:{" "}
                      {item.lastActivityAt
                        ? formatGeneratedAt(item.lastActivityAt)
                        : "—"}
                    </span>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </section>

        <section className="admin-stats__panel admin-stats-tour-explorers">
          <div className="admin-stats-panel__title-row">
            <h5>
              <Compass size={14} aria-hidden="true" />
              Exploradores
            </h5>
            <span className="admin-stats-panel__badge">{listData?.total ?? 0}</span>
          </div>
          <p className="admin-stats-panel__lede">
            Usuários com progresso registrado na versão {tourVersion}. O número de
            desafios varia conforme permissões de cada pessoa.
          </p>

          <div
            className="admin-stats-tour-filters"
            role="tablist"
            aria-label="Filtrar por status"
          >
            {PORTAL_TOUR_STATUS_FILTERS.map((filter) => (
              <button
                key={filter}
                type="button"
                role="tab"
                aria-selected={statusFilter === filter}
                className={`admin-stats-tour-filters__btn${
                  statusFilter === filter ? " is-active" : ""
                }`}
                onClick={() => setStatusFilter(filter)}
              >
                {PORTAL_TOUR_STATUS_LABELS[filter]}
              </button>
            ))}
          </div>

          {loading && !items.length ? (
            <p className="admin-stats__empty">Carregando exploradores…</p>
          ) : error && !items.length ? (
            <p className="admin-stats__empty">{error}</p>
          ) : items.length === 0 ? (
            <p className="admin-stats__empty">
              Nenhum usuário com status «{PORTAL_TOUR_STATUS_LABELS[statusFilter]}».
            </p>
          ) : (
            <>
              <ul
                className="admin-stats-least-engaged-list admin-stats-tour-explorer-list"
                aria-label="Lista de exploradores do tour"
              >
                {items.map((item) => (
                  <li key={item.userId} className="admin-stats-least-engaged-item">
                    <div className="admin-stats-least-engaged-item__head">
                      <div>
                        <strong>{item.name}</strong>
                        <span className="admin-stats-least-engaged-item__email">
                          {item.email}
                        </span>
                      </div>
                      <div className="admin-stats-least-engaged-item__metrics">
                        <span
                          className={`admin-stats-tour-status admin-stats-tour-status--${item.status}`}
                        >
                          {PORTAL_TOUR_STATUS_LABELS[item.status] ?? item.status}
                        </span>
                        <span>{item.completedQuestCount} desafios</span>
                      </div>
                    </div>
                    <div className="admin-stats-least-engaged-item__meta">
                      <span>Início: {formatGeneratedAt(item.startedAt)}</span>
                      <span>
                        Última atividade: {formatGeneratedAt(item.lastActivityAt)}
                      </span>
                      {item.completedAt ? (
                        <span>Concluiu: {formatGeneratedAt(item.completedAt)}</span>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>

              {listData && listData.total > pageSize ? (
                <nav
                  className="admin-stats-tour-pagination"
                  aria-label="Paginação de exploradores"
                >
                  <button
                    type="button"
                    className="admin-stats-tour-pagination__btn"
                    disabled={!canGoPrev || loading}
                    onClick={() => setPage((current) => Math.max(0, current - 1))}
                  >
                    Anterior
                  </button>
                  <span className="admin-stats-tour-pagination__info">
                    Página {page + 1} de {totalPages} · {listData.total} registros
                  </span>
                  <button
                    type="button"
                    className="admin-stats-tour-pagination__btn"
                    disabled={!canGoNext || loading}
                    onClick={() => setPage((current) => current + 1)}
                  >
                    Próxima
                  </button>
                </nav>
              ) : null}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
