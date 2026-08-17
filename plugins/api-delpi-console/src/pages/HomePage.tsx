import { useCallback, useState } from "react";
import type { MetricKpiCardTone } from "@delpi/plugin-ui";
import {
  Activity,
  Bell,
  BookOpen,
  CheckCircle2,
  Database,
  FileJson,
  ShieldCheck,
  Terminal,
  XCircle,
} from "lucide-react";
import { ConsoleMetricKpiCard, ConsoleSectionCard } from "../app/consoleUi";
import { MONITOR_REFRESH_MS } from "../constants/monitoring";
import { fetchConsoleHealth, type ConsoleHealthPayload } from "../lib/consoleAlerts";
import { fetchHealth, type ApiFetchResult } from "../api/httpClient";
import { usePolling } from "../lib/usePolling";

type Props = {
  onNavigate: (segment: string, searchParams?: Record<string, string | null | undefined>) => void;
};

function statusClass(status: ConsoleHealthPayload["status"] | undefined): string {
  if (status === "critical") return "adc-health__err";
  if (status === "warning") return "adc-health__warn";
  return "adc-health__ok";
}

function formatPct(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toFixed(value >= 10 ? 0 : 1)}%`;
}

function formatMs(value: number | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Math.round(value)} ms`;
}

function p95Tone(health: ConsoleHealthPayload): MetricKpiCardTone {
  const p95 = health.metrics.p95_ms;
  const threshold = health.thresholds.p95_ms;
  if (!threshold || !health.traffic?.total_requests) return "default";
  if (p95 >= threshold) return "negative";
  return "positive";
}

function alertTone(health: ConsoleHealthPayload): MetricKpiCardTone {
  if (health.status === "critical") return "negative";
  if (health.status === "warning" || health.open_alert_count > 0) return "warning";
  return "positive";
}

function ConsoleHealthGlance({
  health,
  onNavigate,
}: {
  health: ConsoleHealthPayload;
  onNavigate: Props["onNavigate"];
}) {
  const requests = health.traffic?.total_requests ?? health.metrics.caller_requests ?? 0;
  const emptyWindow = requests <= 0;

  return (
    <ConsoleSectionCard
      title="Glance operacional"
      subtitle="RED da janela amostrada (polling 30 s) — saturação e alertas vêm do contrato da API."
      actions={
        <button type="button" className="adc-link" onClick={() => onNavigate("alertas")}>
          Ver alertas
        </button>
      }
    >
      {emptyWindow ? (
        <p className="adc-muted">Sem tráfego na janela.</p>
      ) : null}
      <div className="adc-glance-kpis" role="group" aria-label="Métricas RED do console">
        <ConsoleMetricKpiCard
          label="Requisições"
          value={emptyWindow ? "—" : String(requests)}
          hint="Janela em memória"
          tone="default"
        />
        <ConsoleMetricKpiCard
          label="Erros"
          value={emptyWindow ? "—" : formatPct(health.traffic?.error_rate_pct ?? health.metrics.error_rate_pct)}
          hint={
            emptyWindow
              ? "Sem amostras"
              : `${health.traffic?.error_count ?? 0} com status ≥ 400`
          }
          tone="default"
        />
        <ConsoleMetricKpiCard
          label="p95"
          value={emptyWindow ? "—" : formatMs(health.metrics.p95_ms)}
          hint={emptyWindow ? "Sem amostras" : `Limiar ${formatMs(health.thresholds.p95_ms)}`}
          tone={p95Tone(health)}
        />
        <ConsoleMetricKpiCard
          label="Pool"
          value={formatPct(health.metrics.pool_occupancy_pct ?? health.pools?.max_occupancy_pct)}
          hint="Máx. ocupação Plugins/TOTVS"
          tone="default"
          titleHint="Detalhe dos pools na aba Cache"
        />
        <ConsoleMetricKpiCard
          label="Alertas"
          value={String(health.open_alerts_count ?? health.open_alert_count)}
          hint={health.status}
          tone={alertTone(health)}
        />
      </div>
    </ConsoleSectionCard>
  );
}

export function HomePage({ onNavigate }: Props) {
  const [health, setHealth] = useState<ApiFetchResult | null>(null);
  const [consoleHealth, setConsoleHealth] = useState<ConsoleHealthPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [apiHealth, monitorHealth] = await Promise.all([fetchHealth(), fetchConsoleHealth()]);
      setHealth(apiHealth);
      setConsoleHealth(monitorHealth);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao verificar saúde");
    } finally {
      setLoading(false);
    }
  }, []);

  usePolling(refresh, MONITOR_REFRESH_MS, { immediate: true });

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header">
        <div>
          <h1>Console API DELPI</h1>
          <p className="adc-subtitle">
            Documentação interativa, OpenAPI e monitoramento contínuo da api-delpi (polling 30 s).
          </p>
        </div>
      </header>

      {consoleHealth ? (
        <div className="adc-glance">
          <ConsoleHealthGlance health={consoleHealth} onNavigate={onNavigate} />
        </div>
      ) : loading ? (
        <p className="adc-muted">Carregando glance operacional…</p>
      ) : null}

      <section className="adc-card-grid">
        <article className="adc-card">
          <div className="adc-card__icon">
            <Activity size={22} />
          </div>
          <h2>Saúde da API</h2>
          {loading && !health ? (
            <p className="adc-muted">Verificando /health…</p>
          ) : error ? (
            <p className="adc-error">{error}</p>
          ) : health ? (
            <div className="adc-health">
              {health.ok ? (
                <CheckCircle2 className="adc-health__ok" size={20} />
              ) : (
                <XCircle className="adc-health__err" size={20} />
              )}
              <span>
                {health.ok ? "Online" : "Indisponível"} — HTTP {health.status} em{" "}
                {health.durationMs} ms
              </span>
            </div>
          ) : null}
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("alertas")}>
          <div className="adc-card__icon">
            <Bell size={22} />
          </div>
          <h2>Monitoramento</h2>
          {consoleHealth ? (
            <div className="adc-health">
              <Activity className={statusClass(consoleHealth.status)} size={20} />
              <span>
                {consoleHealth.status} — {consoleHealth.open_alert_count} alerta(s) · p95{" "}
                {consoleHealth.metrics.p95_ms} ms
              </span>
            </div>
          ) : (
            <p className="adc-muted">Carregando telemetria do console…</p>
          )}
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("documentacao")}>
          <div className="adc-card__icon">
            <BookOpen size={22} />
          </div>
          <h2>Documentação da API</h2>
          <p>Referência interativa de rotas com teste de endpoints e JWT do portal.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("verificacoes")}>
          <div className="adc-card__icon">
            <ShieldCheck size={22} />
          </div>
          <h2>Verificações</h2>
          <p>Smoke suite das rotas críticas — LMP, estoque, qualidade e saúde.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("sql")}>
          <div className="adc-card__icon">
            <Activity size={22} />
          </div>
          <h2>Saúde SQL</h2>
          <p>Top queries por duração e repetição — telemetria do Protheus ao vivo.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("cache")}>
          <div className="adc-card__icon">
            <Database size={22} />
          </div>
          <h2>Cache, callers e pools</h2>
          <p>Hits/miss LMP e estoque, callers, connection pools e comparador de deploy.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("explorer")}>
          <div className="adc-card__icon">
            <Terminal size={22} />
          </div>
          <h2>Explorador de rotas</h2>
          <p>Executa endpoints com params, exemplos do schema e painel de resposta.</p>
        </article>

        <article className="adc-card adc-card--action" onClick={() => onNavigate("spec")}>
          <div className="adc-card__icon">
            <FileJson size={22} />
          </div>
          <h2>OpenAPI / Spec</h2>
          <p>Inventário por tag, contagem de operações e download do JSON.</p>
        </article>
      </section>

      <section className="adc-panel adc-panel--info">
        <h3>Como funciona o monitoramento</h3>
        <p>
          O console <strong>não usa WebSocket</strong> — ele faz <strong>polling a cada 30 segundos</strong>{" "}
          enquanto a aba está visível. A telemetria SQL e HTTP é alimentada pelo tráfego real na{" "}
          <code>api-delpi</code> (dashboards, smoke, explorador). Alertas críticos podem ir para o{" "}
          <strong>sino da Minha DELPI</strong> (usuários com acesso ao console) e/ou webhook externo.
        </p>
        <p className="adc-muted">
          Roadmap: <code>api-delpi/docs/roadmaps/playbook-api-delpi-console.md</code>
        </p>
      </section>
    </div>
  );
}
