import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CalendarCheck,
  CheckCircle2,
  PiggyBank,
  Sparkles,
  TrendingUp,
  Wrench,
} from "lucide-react";

import { fetchKaizenSummary } from "../api/kaizenApi";
import { BarList, type BarListBucket, type BarListTone } from "../components/BarList";
import { KaizenNavTabs } from "../components/KaizenNavTabs";
import { KaizenPageHeader } from "../components/KaizenPageHeader";
import {
  EmptyHint,
  FilterInputField,
  FiltersRow,
  KpiCard,
  MultiSelectField,
  StateAlert,
} from "../components/ui";
import { BRANCHES, detailPath, newPath } from "../constants/kaizen";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useCompetenceLinkedDates } from "../hooks/useCompetenceLinkedDates";
import type { KaizenSummary, KaizenSummaryBucket } from "../types/kaizen";
import {
  readDashboardFilters,
  subscribeDashboardFilterSync,
  writeDashboardFilters,
} from "../utils/dashboardFilterUrl";
import { formatCurrency, formatDate, formatInteger } from "../utils/format";
import { savingsTypeLabel, statusLabel, unitLabel } from "../utils/labels";
import { KZ_GHOST_BTN } from "../components/ui/ghostChrome";

type Props = {
  onNavigate: (path: string) => void;
};

type Tone = BarListTone;

type Bucket = BarListBucket;

const STATUS_TONE: Record<string, Tone> = {
  implantado: "success",
  aprovado: "accent",
  recebido: "accent",
  descontinuado: "muted",
  cancelado: "danger",
};

const UNIT_OPTIONS = BRANCHES.map((item) => ({ value: item.code, label: item.label }));

function unitsFromString(value: string): string[] {
  return value ? value.split(",").filter(Boolean) : [];
}

const MONTH_FMT = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "numeric" });

function monthLabel(key: string): string {
  const [year, month] = key.split("-").map(Number);
  if (!year || !month) return key;
  return MONTH_FMT.format(new Date(year, month - 1, 1));
}

function categoryLabel(key: string): string {
  return key === "sem_categoria" ? "Sem categoria" : key;
}

function withLabels(buckets: KaizenSummaryBucket[], labelOf: (key: string) => string): Bucket[] {
  return buckets.map((bucket) => ({ key: bucket.key, label: labelOf(bucket.key), value: bucket.value }));
}

export function KaizenDashboardPage({ onNavigate }: Props) {
  const initialFilters = useMemo(() => readDashboardFilters(), []);
  const [summary, setSummary] = useState<KaizenSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [units, setUnits] = useState<string[]>(unitsFromString(initialFilters.unit));

  const {
    dateStart,
    dateEnd,
    competence,
    setCompetence,
    setDateStart,
    setDateEnd,
    replaceAll,
    reset,
  } = useCompetenceLinkedDates({
    dateStart: initialFilters.dateStart,
    dateEnd: initialFilters.dateEnd,
    competence: initialFilters.competence,
  });

  // O backend filtra por uma unidade (^(01|02)$). Com uma selecionada, filtra; com
  // nenhuma ou todas, consolida (sem branch).
  const branchParam = units.length === 1 ? units[0] : undefined;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchKaizenSummary({
        branch: branchParam,
        dateStart: dateStart || undefined,
        dateEnd: dateEnd || undefined,
      });
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar indicadores.");
    } finally {
      setLoading(false);
    }
  }, [branchParam, dateStart, dateEnd]);

  useEffect(() => {
    void load();
  }, [load]);

  // Reflete os filtros na URL (compartilhável) e no sessionStorage (troca de aba no portal).
  useEffect(() => {
    writeDashboardFilters({ unit: units.join(","), dateStart, dateEnd, competence });
  }, [units, dateStart, dateEnd, competence]);

  // Navegação voltar/avançar do navegador re-aplica os filtros da URL.
  useEffect(() => {
    return subscribeDashboardFilterSync(() => {
      const next = readDashboardFilters();
      setUnits(unitsFromString(next.unit));
      replaceAll({
        dateStart: next.dateStart,
        dateEnd: next.dateEnd,
        competence: next.competence,
      });
    });
  }, [replaceAll]);

  const hasFilters = Boolean(units.length || dateStart || dateEnd || competence);

  const clearFilters = useCallback(() => {
    setUnits([]);
    reset();
  }, [reset]);

  const buckets = useMemo(() => {
    if (!summary) return null;
    return {
      implantedByMonth: withLabels(summary.implanted_by_month, monthLabel),
      byStatus: withLabels(summary.by_status, (key) => statusLabel(key)),
      byBranch: withLabels(summary.by_branch, (key) => unitLabel(key)),
      bySavingsType: withLabels(summary.by_savings_type, (key) => savingsTypeLabel(key)),
      byCategory: withLabels(summary.by_category, categoryLabel),
      topAccountables: withLabels(summary.top_accountables, (key) => key),
    };
  }, [summary]);

  const hasPeriod = summary?.has_period ?? false;
  const savingsHint = hasPeriod ? "no período selecionado" : "acumulado (validade de 1 ano)";
  const implantedHint = hasPeriod ? "no período selecionado" : "total aprovados/implantados";

  const total = summary?.total ?? 0;
  const showEmptyCatalog =
    summary != null &&
    !error &&
    !hasFilters &&
    total === 0 &&
    (summary.implantados ?? 0) === 0 &&
    (summary.aprovados ?? 0) === 0;
  const showPeriodWithoutNewImplants =
    summary != null &&
    hasPeriod &&
    total === 0 &&
    summary.period_implanted_count === 0 &&
    (summary.period_savings > 0 || summary.active_count > 0);
  const showDashboard = summary != null && !error && !showEmptyCatalog;

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
              className={KZ_GHOST_BTN}
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

      <FiltersRow
        ariaLabel="Filtros do painel"
        trailing={
          hasFilters ? (
            <button type="button" className={KZ_GHOST_BTN} onClick={clearFilters}>
              Limpar filtros
            </button>
          ) : undefined
        }
      >
        <MultiSelectField
          label="Unidade"
          labelHint={KAIZEN_HELP_TOOLTIPS.fields.branch}
          options={UNIT_OPTIONS}
          selectedValues={units}
          onChange={setUnits}
          emptyLabel="Todas"
        />
        <FilterInputField
          id="kz-dash-competence"
          label="Competência"
          hint="Mês de referência. Preenche automaticamente as datas inicial e final."
          type="month"
          value={competence}
          onChange={setCompetence}
        />
        <FilterInputField
          id="kz-dash-date-start"
          label="Data inicial"
          hint="Início do período considerado nos indicadores."
          type="date"
          value={dateStart}
          onChange={setDateStart}
        />
        <FilterInputField
          id="kz-dash-date-end"
          label="Data final"
          hint="Fim do período considerado nos indicadores."
          type="date"
          value={dateEnd}
          onChange={setDateEnd}
        />
      </FiltersRow>

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {loading && !summary ? <StateAlert>Carregando indicadores…</StateAlert> : null}

      {showEmptyCatalog ? (
        <StateAlert>Nenhum kaizen cadastrado ainda.</StateAlert>
      ) : null}

      {showPeriodWithoutNewImplants ? (
        <p className="kz-dash-period-note" role="status">
          Nenhum kaizen implantado no período. Ganhos e ativos abaixo incluem kaizens já em
          operação.
        </p>
      ) : null}

      {showDashboard && buckets ? (
        <>
          <section className="kz-kpi-grid">
            <KpiCard
              icon={<PiggyBank size={22} />}
              tone="success"
              label="Ganhos financeiros"
              value={formatCurrency(summary.period_savings)}
              sub={savingsHint}
            />
            <KpiCard
              icon={<CalendarCheck size={22} />}
              tone="accent"
              label="Kaizens aprovados/implantados"
              value={formatInteger(summary.period_implanted_count)}
              sub={implantedHint}
            />
            <KpiCard
              icon={<Sparkles size={22} />}
              tone="accent"
              label="Total de kaizens"
              value={formatInteger(summary.total)}
              sub={`${formatInteger(summary.aprovados ?? 0)} aprovados · ${formatInteger(summary.implantados)} implantados`}
            />
            <KpiCard
              icon={<TrendingUp size={22} />}
              tone="success"
              label="Ganho anual vigente"
              value={formatCurrency(summary.active_annual_savings)}
              sub={`${formatInteger(summary.active_count)} kaizens contabilizando`}
            />
            <KpiCard
              icon={<CheckCircle2 size={22} />}
              tone="muted"
              label="Ganho realizado / ano"
              value={formatCurrency(summary.realized_annual_savings)}
              sub="Economia efetivamente medida"
            />
            <KpiCard
              icon={<Wrench size={22} />}
              tone="muted"
              label="Investimento total"
              value={formatCurrency(summary.total_investment)}
              sub="Somatório dos cadastros"
            />
          </section>

          <div className="kz-dash-grid">
            <section className="kz-card kz-dash-panel kz-dash-panel--wide">
              <h2 className="kz-dash-panel__title">Kaizens aprovados/implantados por mês</h2>
              <BarList buckets={buckets.implantedByMonth} toneOf={() => "success"} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por situação</h2>
              <BarList buckets={buckets.byStatus} toneOf={(b) => STATUS_TONE[b.key] ?? "accent"} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por unidade</h2>
              <BarList buckets={buckets.byBranch} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por tipo de economia</h2>
              <BarList buckets={buckets.bySavingsType} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Por categoria</h2>
              <BarList buckets={buckets.byCategory} />
            </section>

            <section className="kz-card kz-dash-panel">
              <h2 className="kz-dash-panel__title">Responsáveis mais ativos</h2>
              <BarList buckets={buckets.topAccountables} toneOf={() => "muted"} />
            </section>

            <section className="kz-card kz-dash-panel kz-dash-panel--validity">
              <h2 className="kz-dash-panel__title">
                <AlertTriangle size={16} aria-hidden="true" />
                Validade dos ganhos (1 ano)
              </h2>
              {summary.expired_but_implanted > 0 ? (
                <p className="kz-validity-note kz-validity-note--expired">
                  {formatInteger(summary.expired_but_implanted)} kaizen(s) já passaram de 1 ano e
                  deixaram de contabilizar.
                </p>
              ) : null}
              {summary.expiring_soon.length === 0 ? (
                <EmptyHint>Nenhum ganho expira nos próximos 90 dias.</EmptyHint>
              ) : (
                <ul className="kz-validity-list">
                  {summary.expiring_soon.map((item) => (
                    <li key={item.id} className="kz-validity-row">
                      <button
                        type="button"
                        className="kz-validity-row__link"
                        onClick={() => onNavigate(detailPath(item.id))}
                      >
                        <span className="kz-validity-row__title">{item.title}</span>
                        <span className="kz-validity-row__meta">
                          {unitLabel(item.branch_code)} • vence {formatDate(item.valid_until)}
                        </span>
                      </button>
                      <span
                        className={`kz-validity-badge${
                          item.days_left <= 30 ? " kz-validity-badge--urgent" : ""
                        }`}
                      >
                        {item.days_left <= 0
                          ? "vence hoje"
                          : `${formatInteger(item.days_left)} dias`}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="kz-card kz-dash-panel kz-dash-panel--recent">
              <h2 className="kz-dash-panel__title">Cadastros recentes</h2>
              <ul className="kz-recent-list">
                {summary.recent.map((record) => (
                  <li key={record.id} className="kz-recent-row">
                    <button
                      type="button"
                      className="kz-recent-row__link"
                      onClick={() => onNavigate(detailPath(record.id))}
                    >
                      <span className="kz-recent-row__title">{record.title}</span>
                      <span className="kz-recent-row__meta">
                        {unitLabel(record.branch_code)} • {statusLabel(record.status)}
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
