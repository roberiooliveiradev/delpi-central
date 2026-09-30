import { Gauge } from "lucide-react";
import type { ReactNode } from "react";
import type { MesPerformance } from "../../types/mes";
import { formatHoursMinutes } from "../../utils/dayTimeline";
import {
  ACTUAL_CYCLE_HELP,
  PERFORMANCE_HELP,
  formatCycleSeconds,
  formatPerformancePercent,
  formatPiecesPerHour,
  performancePaceLabel,
  performanceQualityHint,
  standardTimeSourceLabel,
} from "../../utils/performance";

/** Valor principal + contexto curto — usado no card do Monitoramento. */
export function PerformanceStrip({ performance }: { performance: MesPerformance | null | undefined }) {
  if (!performance) return null;
  const hint = performanceQualityHint(performance.dataQuality);
  const pace = performancePaceLabel(performance.performancePercent);
  const percent = formatPerformancePercent(performance.performancePercent);
  return (
    <div className="delpi-mes-perf" title={PERFORMANCE_HELP}>
      <span className="delpi-mes-perf__head">
        <span className="delpi-mes-perf__label">Performance</span>
        <strong className="delpi-mes-perf__value">{percent}</strong>
        {pace ? <span className="delpi-mes-perf__pace">{pace}</span> : null}
      </span>
      {hint && performance.performancePercent == null ? (
        <span className="delpi-mes-perf__hint" role="note" title={hint.detail}>
          {hint.short}
        </span>
      ) : null}
      {performance.idealCycleSeconds != null || performance.actualAverageCycleSeconds != null ? (
        <span className="delpi-mes-perf__line" title={ACTUAL_CYCLE_HELP}>
          Ciclo {formatCycleSeconds(performance.idealCycleSeconds)} padrão · {formatCycleSeconds(performance.actualAverageCycleSeconds)} real
        </span>
      ) : null}
      {performance.actualThroughputPerHour != null || performance.expectedThroughputPerHour != null ? (
        <span className="delpi-mes-perf__line">
          Ritmo {formatPiecesPerHour(performance.actualThroughputPerHour)} · esperado {formatPiecesPerHour(performance.expectedThroughputPerHour)}
        </span>
      ) : null}
    </div>
  );
}

function Row({ label, value, title }: { label: string; value: ReactNode; title?: string }) {
  return (
    <div className="delpi-mes-perf-panel__row" title={title}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

/** Painel completo do run — página de detalhe do CT. */
export function RunPerformancePanel({
  performance,
  idealProductionSeconds,
  loading,
  error,
  onRetry,
}: {
  performance: MesPerformance | null | undefined;
  idealProductionSeconds?: number | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}) {
  const hint = performanceQualityHint(performance?.dataQuality);
  const pace = performancePaceLabel(performance?.performancePercent);
  return (
    <section className="delpi-mes-panel delpi-mes-perf-panel" aria-labelledby="delpi-mes-perf-title">
      <header className="delpi-mes-panel__head">
        <div>
          <h3 id="delpi-mes-perf-title">
            <Gauge aria-hidden="true" /> Performance do run atual
          </h3>
          <p>{PERFORMANCE_HELP}</p>
        </div>
      </header>

      {performance ? (
        <div className="delpi-mes-perf-panel__body">
          <div className="delpi-mes-perf-panel__hero">
            <strong className="delpi-mes-perf-panel__percent">
              {formatPerformancePercent(performance.performancePercent)}
            </strong>
            {pace ? <span className="delpi-mes-perf__pace">{pace}</span> : null}
          </div>

          {hint ? (
            <p className="delpi-mes-perf-panel__quality" role="note">
              {performance.performancePercent == null ? "Performance indisponível. " : ""}
              {hint.detail}
            </p>
          ) : null}

          <div className="delpi-mes-perf-panel__grid">
            <Row label="Ciclo padrão" value={formatCycleSeconds(performance.idealCycleSeconds) + "/peça"} />
            <Row label="Ciclo médio real" value={formatCycleSeconds(performance.actualAverageCycleSeconds) + "/peça"} title={ACTUAL_CYCLE_HELP} />
            <Row label="Ritmo real" value={formatPiecesPerHour(performance.actualThroughputPerHour)} />
            <Row label="Ritmo esperado" value={formatPiecesPerHour(performance.expectedThroughputPerHour)} />
            <Row label="Tempo produzindo" value={formatHoursMinutes(performance.producingSeconds)} />
            <Row
              label="Tempo ideal previsto"
              value={loading && idealProductionSeconds == null ? "…" : idealProductionSeconds != null ? formatHoursMinutes(idealProductionSeconds) : "—"}
            />
            <Row label="Peças produzidas" value={performance.producedPieces} />
            <Row label="Origem do tempo padrão" value={standardTimeSourceLabel(performance.standardTimeSource)} />
          </div>

          {error ? (
            <p className="delpi-mes-monitoring__stale" role="status">
              Não foi possível carregar o tempo ideal previsto.{" "}
              {onRetry ? <button type="button" onClick={onRetry}>Tentar novamente</button> : null}
            </p>
          ) : null}
        </div>
      ) : loading ? (
        <p className="delpi-mes-panel__empty" role="status">Carregando Performance do run…</p>
      ) : error ? (
        <p className="delpi-mes-monitoring__stale" role="alert">
          Não foi possível carregar os dados de Performance.{" "}
          {onRetry ? <button type="button" onClick={onRetry}>Tentar novamente</button> : null}
        </p>
      ) : null}
    </section>
  );
}
