import { useEffect, useMemo, useState } from "react";
import {
  CalendarClock,
  CheckCircle2,
  FileText,
  Plus,
  Send,
} from "lucide-react";

import {
  getReportSchedule,
  listReportDefinitions,
  listReportRuns,
} from "../api/reportsApi";
import type { ReportDefinition, ReportRun, ReportSchedule } from "../types/reports";
import { formatDateTimeBr } from "../utils/format";
import {
  definitionPath,
  REPORTS_LIST_PATH,
  REPORTS_NEW_PATH,
} from "../utils/route";

type UpcomingItem = {
  definition: ReportDefinition;
  schedule: ReportSchedule;
};

function startOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function daysAgo(n: number): Date {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return d;
}

function dayKey(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString().slice(0, 10);
}

function scheduleFrequencyLabel(schedule: ReportSchedule | null | undefined): string {
  if (!schedule) return "—";
  if (schedule.scheduleKind === "weekly") return "Semanal";
  if (schedule.scheduleKind === "weekdays") return "Dias úteis";
  if (schedule.scheduleKind === "daily") return "Diária";
  return schedule.scheduleKind || "—";
}

function buildSeries(runs: ReportRun[], days = 30): Array<{ key: string; count: number }> {
  const start = daysAgo(days - 1);
  const map = new Map<string, number>();
  for (let i = 0; i < days; i += 1) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    map.set(d.toISOString().slice(0, 10), 0);
  }
  for (const run of runs) {
    const key = dayKey(run.createdAt ?? run.startedAt);
    if (!key || !map.has(key)) continue;
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return Array.from(map.entries()).map(([key, count]) => ({ key, count }));
}

function SparkAreaChart({ series }: { series: Array<{ key: string; count: number }> }) {
  const width = 640;
  const height = 220;
  const padX = 12;
  const padY = 16;
  const max = Math.max(1, ...series.map((p) => p.count));
  const points = series.map((point, index) => {
    const x =
      padX +
      (series.length <= 1
        ? (width - padX * 2) / 2
        : (index / (series.length - 1)) * (width - padX * 2));
    const y = height - padY - (point.count / max) * (height - padY * 2);
    return { x, y, ...point };
  });
  const line = points.map((p) => `${p.x},${p.y}`).join(" ");
  const area = [
    `${padX},${height - padY}`,
    ...points.map((p) => `${p.x},${p.y}`),
    `${width - padX},${height - padY}`,
  ].join(" ");
  const firstLabel = series[0]?.key
    ? new Date(`${series[0].key}T12:00:00`).toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
      })
    : "";
  const lastLabel = series[series.length - 1]?.key
    ? new Date(`${series[series.length - 1].key}T12:00:00`).toLocaleDateString(
        "pt-BR",
        { day: "2-digit", month: "2-digit" },
      )
    : "";

  return (
    <div className="rp-spark-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Envios nos últimos 30 dias">
        <defs>
          <linearGradient id="rpSparkFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--rp-blue-accent)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--rp-blue-accent)" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#rpSparkFill)" />
        <polyline
          points={line}
          fill="none"
          stroke="var(--rp-blue-700)"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      </svg>
      <div className="rp-spark-chart__axis">
        <span>{firstLabel}</span>
        <span>{lastLabel}</span>
      </div>
    </div>
  );
}

export function OverviewPage() {
  const [definitions, setDefinitions] = useState<ReportDefinition[]>([]);
  const [runs, setRuns] = useState<ReportRun[]>([]);
  const [schedulesById, setSchedulesById] = useState<
    Record<string, ReportSchedule | null>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [defsPayload, runsPayload] = await Promise.all([
          listReportDefinitions(controller.signal),
          listReportRuns(undefined, controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setDefinitions(defsPayload.items);
        setRuns(runsPayload.items);

        const scheduleEntries = await Promise.all(
          defsPayload.items.map(async (def) => {
            try {
              const schedule = await getReportSchedule(def.id, controller.signal);
              return [def.id, schedule] as const;
            } catch {
              return [def.id, null] as const;
            }
          }),
        );
        if (controller.signal.aborted) return;
        setSchedulesById(Object.fromEntries(scheduleEntries));
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar a visão geral.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void load();
    return () => controller.abort();
  }, []);

  const activeCount = definitions.filter((d) => d.active).length;
  const inactiveCount = definitions.length - activeCount;

  const enabledSchedules = useMemo(() => {
    return Object.values(schedulesById).filter((s) => s?.enabled).length;
  }, [schedulesById]);

  const monthRuns = useMemo(() => {
    const start = startOfMonth(new Date()).getTime();
    return runs.filter((run) => {
      const raw = run.createdAt ?? run.startedAt;
      if (!raw) return false;
      const t = new Date(raw).getTime();
      return !Number.isNaN(t) && t >= start;
    });
  }, [runs]);

  const successRate = useMemo(() => {
    if (monthRuns.length === 0) return null;
    const ok = monthRuns.filter((r) => r.status === "succeeded").length;
    return (ok / monthRuns.length) * 100;
  }, [monthRuns]);

  const series = useMemo(() => buildSeries(runs, 30), [runs]);

  const upcoming = useMemo(() => {
    const items: UpcomingItem[] = [];
    for (const def of definitions) {
      const schedule = schedulesById[def.id];
      if (!schedule) continue;
      items.push({ definition: def, schedule });
    }
    return items
      .filter((item) => item.schedule.nextRunAt || !item.schedule.enabled)
      .sort((a, b) => {
        const ta = a.schedule.nextRunAt
          ? new Date(a.schedule.nextRunAt).getTime()
          : Number.POSITIVE_INFINITY;
        const tb = b.schedule.nextRunAt
          ? new Date(b.schedule.nextRunAt).getTime()
          : Number.POSITIVE_INFINITY;
        return ta - tb;
      })
      .slice(0, 5);
  }, [definitions, schedulesById]);

  const recent = definitions.slice(0, 8);

  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>Visão geral</h1>
                </div>
                <p className="rp-page-header__subtitle">
                  Acompanhe relatórios ativos, agendas e envios recentes.
                </p>
              </div>
            </div>
            <div className="rp-page-header__actions">
              <a className="rp-btn rp-btn--primary" href={REPORTS_NEW_PATH}>
                <Plus size={16} aria-hidden />
                Novo relatório
              </a>
            </div>
          </div>
          <div className="rp-page-header__brand-bar" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </div>
      </header>

      {loading ? <p className="rp-banner">Carregando visão geral…</p> : null}
      {error ? (
        <p className="rp-banner rp-banner--error" role="alert">
          {error}
        </p>
      ) : null}

      {!loading && !error ? (
        <>
          <section className="rp-kpi-grid" aria-label="Indicadores">
            <article className="rp-kpi-card">
              <div className="rp-kpi-card__top">
                <span className="rp-kpi-card__icon">
                  <FileText size={18} aria-hidden />
                </span>
                <span className="rp-kpi-card__label">Relatórios ativos</span>
              </div>
              <strong className="rp-kpi-card__value">{activeCount}</strong>
              <p className="rp-kpi-card__foot">
                {inactiveCount > 0
                  ? `${inactiveCount} inativo(s)`
                  : "Todos ativos"}
              </p>
            </article>

            <article className="rp-kpi-card">
              <div className="rp-kpi-card__top">
                <span className="rp-kpi-card__icon">
                  <CalendarClock size={18} aria-hidden />
                </span>
                <span className="rp-kpi-card__label">Agendamentos</span>
              </div>
              <strong className="rp-kpi-card__value">{enabledSchedules}</strong>
              <p className="rp-kpi-card__foot">
                {definitions.length === 0
                  ? "Sem definições"
                  : `${enabledSchedules} habilitado(s)`}
              </p>
            </article>

            <article className="rp-kpi-card">
              <div className="rp-kpi-card__top">
                <span className="rp-kpi-card__icon">
                  <Send size={18} aria-hidden />
                </span>
                <span className="rp-kpi-card__label">Envios este mês</span>
              </div>
              <strong className="rp-kpi-card__value">
                {monthRuns.length.toLocaleString("pt-BR")}
              </strong>
              <p className="rp-kpi-card__foot">
                {runs.length} no histórico carregado
              </p>
            </article>

            <article className="rp-kpi-card">
              <div className="rp-kpi-card__top">
                <span className="rp-kpi-card__icon">
                  <CheckCircle2 size={18} aria-hidden />
                </span>
                <span className="rp-kpi-card__label">Taxa de sucesso</span>
              </div>
              <strong className="rp-kpi-card__value">
                {successRate == null
                  ? "—"
                  : `${successRate.toLocaleString("pt-BR", {
                      maximumFractionDigits: 1,
                    })}%`}
              </strong>
              <p className="rp-kpi-card__foot">
                {monthRuns.length === 0
                  ? "Sem envios no mês"
                  : `Com base em ${monthRuns.length} envio(s)`}
              </p>
            </article>
          </section>

          <section className="rp-overview-grid">
            <article className="rp-card">
              <div className="rp-card__header">
                <div>
                  <h2 className="rp-card__title">Envios nos últimos 30 dias</h2>
                  <p className="rp-card__hint">
                    Agregação diária das execuções registradas.
                  </p>
                </div>
              </div>
              {series.every((p) => p.count === 0) ? (
                <p className="rp-empty">Nenhum envio nos últimos 30 dias.</p>
              ) : (
                <SparkAreaChart series={series} />
              )}
            </article>

            <article className="rp-card">
              <div className="rp-card__header">
                <div>
                  <h2 className="rp-card__title">Próximos envios</h2>
                  <p className="rp-card__hint">Agendas com próximo disparo.</p>
                </div>
                <a className="rp-btn rp-btn--ghost" href={REPORTS_LIST_PATH}>
                  Ver todos
                </a>
              </div>
              {upcoming.length === 0 ? (
                <p className="rp-empty">Nenhuma agenda configurada.</p>
              ) : (
                <ul className="rp-upcoming-list">
                  {upcoming.map(({ definition, schedule }) => (
                    <li key={definition.id} className="rp-upcoming-list__item">
                      <div className="rp-upcoming-list__main">
                        <a href={definitionPath(definition.id)}>
                          <strong>{definition.name}</strong>
                        </a>
                        <span className="rp-muted">
                          {formatDateTimeBr(schedule.nextRunAt)}
                        </span>
                      </div>
                      <span
                        className={
                          schedule.enabled
                            ? "rp-pill rp-pill--success"
                            : "rp-pill rp-pill--muted"
                        }
                      >
                        {schedule.enabled ? "Agendado" : "Pausado"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </section>

          <section className="rp-card">
            <div className="rp-card__header">
              <div>
                <h2 className="rp-card__title">Relatórios recentes</h2>
                <p className="rp-card__hint">Definições cadastradas no plugin.</p>
              </div>
              <a className="rp-btn rp-btn--ghost" href={REPORTS_LIST_PATH}>
                Ver todos
              </a>
            </div>
            {recent.length === 0 ? (
              <p className="rp-empty">
                Nenhuma definição ainda. Crie o primeiro relatório.
              </p>
            ) : (
              <div className="rp-table-wrap">
                <table className="rp-table">
                  <thead>
                    <tr>
                      <th>Relatório</th>
                      <th>Frequência</th>
                      <th>Próximo envio</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((def) => {
                      const schedule = schedulesById[def.id];
                      return (
                        <tr key={def.id}>
                          <td>
                            <a href={definitionPath(def.id)}>{def.name}</a>
                          </td>
                          <td>{scheduleFrequencyLabel(schedule)}</td>
                          <td>
                            {schedule?.enabled
                              ? formatDateTimeBr(schedule.nextRunAt)
                              : "—"}
                          </td>
                          <td>
                            <span
                              className={
                                def.active
                                  ? "rp-pill rp-pill--success"
                                  : "rp-pill rp-pill--muted"
                              }
                            >
                              {def.active ? "Ativo" : "Inativo"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
