import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  PiggyBank,
  Sparkles,
  Wrench,
} from "lucide-react";

import { fetchKaizenRecords } from "../api/kaizenApi";
import { KaizenNavTabs } from "../components/KaizenNavTabs";
import { KaizenPageHeader } from "../components/KaizenPageHeader";
import { StateAlert } from "../components/StateAlert";
import { detailPath, newPath } from "../constants/kaizen";
import type { KaizenRecord } from "../types/kaizen";
import { formatCurrency, formatDate, formatInteger } from "../utils/format";
import { computeKaizenStats, type CountBucket } from "../utils/kaizenStats";
import { statusLabel } from "../utils/labels";

type Props = {
  onNavigate: (path: string) => void;
};

type Tone = "accent" | "success" | "warning" | "danger" | "muted";

const STATUS_TONE: Record<string, Tone> = {
  implantado: "success",
  em_andamento: "accent",
  descontinuado: "muted",
  cancelado: "danger",
};

function BarList({
  buckets,
  toneOf,
}: {
  buckets: CountBucket[];
  toneOf?: (bucket: CountBucket) => Tone;
}) {
  const max = Math.max(1, ...buckets.map((b) => b.value));
  if (buckets.length === 0) {
    return <p className="kz-empty-hint">Sem dados.</p>;
  }
  return (
    <ul className="kz-barlist">
      {buckets.map((bucket) => (
        <li className="kz-barlist__row" key={bucket.key}>
          <span className="kz-barlist__label" title={bucket.label}>
            {bucket.label}
          </span>
          <span className="kz-barlist__track">
            <span
              className={`kz-barlist__fill kz-barlist__fill--${toneOf?.(bucket) ?? "accent"}`}
              style={{ width: `${Math.round((bucket.value / max) * 100)}%` }}
            />
          </span>
          <span className="kz-barlist__value">{formatInteger(bucket.value)}</span>
        </li>
      ))}
    </ul>
  );
}

function KpiCard({
  icon,
  tone,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  tone: Tone;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className={`kz-kpi kz-kpi--${tone}`}>
      <div className="kz-kpi__icon" aria-hidden="true">
        {icon}
      </div>
      <div className="kz-kpi__body">
        <span className="kz-kpi__label">{label}</span>
        <strong className="kz-kpi__value">{value}</strong>
        {sub ? <span className="kz-kpi__sub">{sub}</span> : null}
      </div>
    </div>
  );
}

export function KaizenDashboardPage({ onNavigate }: Props) {
  const [records, setRecords] = useState<KaizenRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKaizenRecords({ page_size: 500 });
      setRecords(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar indicadores.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const stats = useMemo(() => computeKaizenStats(records), [records]);

  return (
    <>
      <KaizenPageHeader
        title="Painel de Kaizens"
        subtitle="Acompanhamento dos cadastros — módulo qualidade"
        nav={<KaizenNavTabs active="dashboard" onNavigate={onNavigate} />}
        actions={
          <>
            <button
              type="button"
              className="kz-ghost-btn"
              onClick={() => void load()}
              disabled={loading}
            >
              {loading ? "Atualizando…" : "Atualizar"}
            </button>
            <button type="button" className="kz-primary-btn" onClick={() => onNavigate(newPath())}>
              Novo kaizen
            </button>
          </>
        }
      />

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && records.length === 0 ? (
        <StateAlert>Carregando indicadores…</StateAlert>
      ) : null}

      {!loading && records.length === 0 && !error ? (
        <StateAlert>Nenhum kaizen cadastrado ainda.</StateAlert>
      ) : null}

      {records.length > 0 ? (
        <>
          <section className="kz-kpi-grid">
            <KpiCard
              icon={<Sparkles size={22} />}
              tone="accent"
              label="Total de kaizens"
              value={formatInteger(stats.total)}
              sub={`${formatInteger(stats.implantados)} implantados`}
            />
            <KpiCard
              icon={<CheckCircle2 size={22} />}
              tone="success"
              label="Ganho anual vigente"
              value={formatCurrency(stats.activeAnnualSavings)}
              sub={`${formatInteger(stats.activeCount)} kaizens contabilizando`}
            />
            <KpiCard
              icon={<PiggyBank size={22} />}
              tone="accent"
              label="Ganho realizado / ano"
              value={formatCurrency(stats.realizedAnnualSavings)}
              sub="Economia efetivamente medida"
            />
            <KpiCard
              icon={<Clock size={22} />}
              tone="warning"
              label="Em andamento"
              value={formatInteger(stats.emAndamento)}
              sub={`${formatInteger(stats.descontinuados + stats.cancelados)} encerrados`}
            />
            <KpiCard
              icon={<Wrench size={22} />}
              tone="muted"
              label="Investimento total"
              value={formatCurrency(stats.totalInvestment)}
              sub="Somatório dos cadastros"
            />
          </section>

          <div className="kz-dash-grid">
            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por situação</h2>
              <BarList buckets={stats.byStatus} toneOf={(b) => STATUS_TONE[b.key] ?? "accent"} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por filial</h2>
              <BarList buckets={stats.byBranch} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por tipo de economia</h2>
              <BarList buckets={stats.bySavingsType} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por categoria</h2>
              <BarList buckets={stats.byCategory} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Responsáveis mais ativos</h2>
              <BarList buckets={stats.topAccountables} toneOf={() => "muted"} />
            </section>

            <section className="kz-card kz-dash-panel kz-dash-panel--validity">
              <h2 className="kz-dash-panel__title">
                <AlertTriangle size={16} aria-hidden="true" />
                Validade dos ganhos (1 ano)
              </h2>
              {stats.expiredButImplanted > 0 ? (
                <p className="kz-validity-note kz-validity-note--expired">
                  {formatInteger(stats.expiredButImplanted)} kaizen(s) já passaram de 1 ano e
                  deixaram de contabilizar.
                </p>
              ) : null}
              {stats.expiringSoon.length === 0 ? (
                <p className="kz-empty-hint">Nenhum ganho expira nos próximos 90 dias.</p>
              ) : (
                <ul className="kz-validity-list">
                  {stats.expiringSoon.map((item) => (
                    <li key={item.record.id} className="kz-validity-row">
                      <button
                        type="button"
                        className="kz-validity-row__link"
                        onClick={() => onNavigate(detailPath(item.record.id))}
                      >
                        <span className="kz-validity-row__title">{item.record.title}</span>
                        <span className="kz-validity-row__meta">
                          Filial {item.record.branch_code} • vence {formatDate(item.validUntil)}
                        </span>
                      </button>
                      <span
                        className={`kz-validity-badge${
                          item.daysLeft <= 30 ? " kz-validity-badge--urgent" : ""
                        }`}
                      >
                        {item.daysLeft <= 0
                          ? "vence hoje"
                          : `${formatInteger(item.daysLeft)} dias`}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="kz-card kz-dash-panel kz-dash-panel--recent">
              <h2 className="kz-dash-panel__title">Cadastros recentes</h2>
              <ul className="kz-recent-list">
                {stats.recent.map((record) => (
                  <li key={record.id} className="kz-recent-row">
                    <button
                      type="button"
                      className="kz-recent-row__link"
                      onClick={() => onNavigate(detailPath(record.id))}
                    >
                      <span className="kz-recent-row__title">{record.title}</span>
                      <span className="kz-recent-row__meta">
                        Filial {record.branch_code} • {statusLabel(record.status)}
                        {record.date_implemented ? ` • ${formatDate(record.date_implemented)}` : ""}
                      </span>
                    </button>
                    <ArrowRight size={15} aria-hidden="true" className="kz-recent-row__chevron" />
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </>
      ) : null}
    </>
  );
}
