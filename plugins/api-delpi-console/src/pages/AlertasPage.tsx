import { useCallback, useState } from "react";
import { Activity, Bell, RefreshCw } from "lucide-react";
import {
  MONITOR_ALERT_EVALUATE_MS,
  MONITOR_REFRESH_MS,
} from "../constants/monitoring";
import {
  alertDetailRows,
  alertGuidance,
  alertSuggestedAction,
} from "../lib/alertPresentation";
import {
  evaluateConsoleAlerts,
  fetchConsoleHealth,
  type ConsoleAlert,
  type ConsoleHealthPayload,
} from "../lib/consoleAlerts";
import { usePolling } from "../lib/usePolling";

export type ConsoleNavigateFn = (
  segment: string,
  searchParams?: Record<string, string | null | undefined>,
) => void;

type Props = {
  onNavigate: ConsoleNavigateFn;
};

function severityClass(severity: string): string {
  if (severity === "critical") return "adc-badge adc-badge--err";
  if (severity === "warning") return "adc-badge adc-badge--warn";
  return "adc-badge adc-badge--ok";
}

function formatCapturedAt(value?: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function AlertasPage({ onNavigate }: Props) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<ConsoleHealthPayload | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [liveMonitor, setLiveMonitor] = useState(true);

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);
    try {
      const payload = await fetchConsoleHealth();
      if (!payload) {
        throw new Error("Falha ao carregar saúde do console");
      }
      setHealth(payload);
    } catch (e) {
      setHealth(null);
      setError(e instanceof Error ? e.message : "Erro ao carregar alertas");
    } finally {
      if (!options?.silent) {
        setLoading(false);
      }
    }
  }, []);

  usePolling(() => load({ silent: true }), MONITOR_REFRESH_MS, {
    enabled: liveMonitor,
    immediate: true,
  });

  usePolling(
    async () => {
      await evaluateConsoleAlerts(true);
      await load({ silent: true });
    },
    MONITOR_ALERT_EVALUATE_MS,
    { enabled: liveMonitor },
  );

  const runEvaluate = async (notify: boolean) => {
    setEvaluating(true);
    try {
      await evaluateConsoleAlerts(notify);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao avaliar alertas");
    } finally {
      setEvaluating(false);
    }
  };

  const renderAlertCard = (alert: ConsoleAlert, key: string) => {
    const rows = alertDetailRows(alert);
    const action = alertSuggestedAction(alert);

    return (
      <article key={key} className="adc-panel adc-panel--alert">
        <div className="adc-toolbar">
          <span className={severityClass(alert.severity)}>{alert.severity}</span>
          <code className="adc-mono-sm">{alert.code}</code>
        </div>
        <p className="adc-alert__message">{alert.message}</p>
        <p className="adc-muted adc-alert__guidance">{alertGuidance(alert)}</p>

        {rows.length > 0 ? (
          <dl className="adc-alert-details">
            {rows.map((row) => (
              <div key={`${key}-${row.label}`} className="adc-alert-details__row">
                <dt>{row.label}</dt>
                <dd>
                  <code className="adc-mono-sm">{row.value}</code>
                </dd>
              </div>
            ))}
          </dl>
        ) : null}

        {action ? (
          <div className="adc-alert__actions">
            <button
              type="button"
              className="adc-btn adc-btn--ghost"
              onClick={() => onNavigate(action.segment, action.searchParams)}
            >
              {action.label}
            </button>
          </div>
        ) : null}
      </article>
    );
  };

  const capturedAt = formatCapturedAt(health?.captured_at);

  return (
    <div className="adc-page adc-page--scroll">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Alertas</h1>
          <p className="adc-subtitle">
            Monitoramento contínuo por polling (30 s) — smoke, p95 e SQL lento. Notificações
            opcionais no sino da Minha DELPI e via webhook.
          </p>
        </div>
        <div className="adc-header__actions">
          <label className="adc-check">
            <input
              type="checkbox"
              checked={liveMonitor}
              onChange={(event) => setLiveMonitor(event.target.checked)}
            />
            Monitoramento ao vivo
          </label>
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "adc-spin" : undefined} />
            Atualizar
          </button>
          <button
            type="button"
            className="adc-btn adc-btn--primary"
            onClick={() => void runEvaluate(true)}
            disabled={evaluating}
          >
            <Bell size={16} />
            Avaliar e notificar
          </button>
        </div>
      </header>

      {health?.monitoring ? (
        <div className="adc-panel adc-panel--info adc-monitor-banner">
          <Activity size={16} aria-hidden />
          <span>
            {liveMonitor
              ? `Atualização automática a cada ${health.monitoring.recommended_refresh_seconds} s com a aba visível.`
              : "Monitoramento automático pausado."}
            {capturedAt ? ` Última captura: ${capturedAt}.` : ""}
          </span>
        </div>
      ) : null}

      {error ? <div className="adc-panel adc-panel--danger">{error}</div> : null}

      {health ? (
        <div className="adc-metrics adc-metrics--grid adc-metrics--compact">
          <div className="adc-stat">
            <span className="adc-stat__label">Status</span>
            <strong>{health.status}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Alertas abertos</span>
            <strong>{health.open_alert_count}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">p95 (ms)</span>
            <strong>
              {health.metrics.p95_ms} / {health.thresholds.p95_ms}
            </strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Amostras SQL</span>
            <strong>{health.metrics.sql_samples}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Webhook</span>
            <strong>{health.webhook_configured ? "Configurado" : "Desligado"}</strong>
          </div>
          <div className="adc-stat">
            <span className="adc-stat__label">Sino Minha DELPI</span>
            <strong>
              {health.portal_notifications_configured ? "Ativo" : "Desligado"}
            </strong>
          </div>
        </div>
      ) : null}

      {loading && !health ? (
        <div className="adc-panel adc-muted">Carregando alertas…</div>
      ) : null}

      {health && health.open_alerts.length > 0 ? (
        <section>
          <h2 className="adc-section-title">Alertas abertos</h2>
          {health.open_alerts.map((alert) =>
            renderAlertCard(alert, `open-${alert.code}-${alert.message}`),
          )}
        </section>
      ) : health ? (
        <div className="adc-panel adc-muted">Nenhum alerta aberto no momento.</div>
      ) : null}

      {health && health.recent_alerts.length > 0 ? (
        <section className="adc-panel adc-panel--table">
          <h2 className="adc-section-title">Histórico recente</h2>
          <div className="adc-table-wrap">
            <table className="adc-table">
              <thead>
                <tr>
                  <th>Severidade</th>
                  <th>Código</th>
                  <th>Detalhe</th>
                  <th>Quando</th>
                  <th>Webhook</th>
                  <th>Sino</th>
                </tr>
              </thead>
              <tbody>
                {health.recent_alerts.map((alert) => {
                  const preview = alertDetailRows(alert).find((row) => row.label === "Query");
                  return (
                    <tr key={`${alert.code}-${alert.recorded_at}`}>
                      <td>
                        <span className={severityClass(alert.severity)}>{alert.severity}</span>
                      </td>
                      <td>
                        <code className="adc-mono-sm">{alert.code}</code>
                      </td>
                      <td className="adc-table__preview">
                        {preview?.value ?? alert.message}
                      </td>
                      <td className="adc-muted">{alert.recorded_at ?? "—"}</td>
                      <td>{alert.notified ? "Sim" : "Não"}</td>
                      <td>{alert.portal_notified ? "Sim" : "Não"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
