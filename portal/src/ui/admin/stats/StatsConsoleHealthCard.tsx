// src/ui/admin/stats/StatsConsoleHealthCard.tsx

import { Bell, ExternalLink } from "lucide-react";

import { useConsoleHealth } from "../../../hooks/useConsoleHealth";
import { StatsMiniKpi, StatsMiniKpiRow } from "./StatsEnrichment";

const CONSOLE_ALERTAS_URL = "/apps/api-delpi-console/alertas";

function statusTone(status: string | undefined): "success" | "warning" | "danger" | "default" {
  if (status === "critical") return "danger";
  if (status === "warning") return "warning";
  if (status === "ok") return "success";
  return "default";
}

function statusLabel(status: string | undefined): string {
  if (status === "critical") return "Crítico";
  if (status === "warning") return "Atenção";
  if (status === "ok") return "Saudável";
  return "—";
}

export function StatsConsoleHealthCard() {
  const { data, loading, error } = useConsoleHealth();

  return (
    <section className="admin-stats__panel admin-stats__panel--console-health">
      <div className="admin-stats-panel__title-row">
        <h5>
          <Bell size={14} aria-hidden="true" />
          Console API DELPI
        </h5>
        <a
          className="admin-stats__panel-link"
          href={CONSOLE_ALERTAS_URL}
          target="_blank"
          rel="noreferrer"
        >
          Abrir alertas
          <ExternalLink size={12} aria-hidden="true" />
        </a>
      </div>
      <p className="admin-stats-panel__lede">
        Smoke, latência p95 e SQL lento — mesma telemetria do plugin api-delpi-console.
      </p>

      {loading && !data ? (
        <p className="admin-stats__empty">Carregando saúde do console…</p>
      ) : null}

      {error && !data ? (
        <p className="admin-stats__empty">{error}</p>
      ) : null}

      {data ? (
        <>
          <StatsMiniKpiRow>
            <StatsMiniKpi
              tone={statusTone(data.status)}
              label="Status"
              value={statusLabel(data.status)}
              hint={`${data.open_alert_count} alerta(s) aberto(s)`}
            />
            <StatsMiniKpi
              label="p95 (ms)"
              value={data.metrics.p95_ms}
              hint={`Limiar ${data.thresholds.p95_ms} ms`}
            />
            <StatsMiniKpi
              label="Requests"
              value={data.metrics.caller_requests}
              hint={`${data.metrics.sql_samples} amostras SQL`}
            />
            <StatsMiniKpi
              label="Cache hit"
              value={`${data.metrics.cache_hit_rate_pct}%`}
              hint={
                data.portal_notifications_configured
                  ? "Sino Minha DELPI ativo"
                  : data.webhook_configured
                    ? "Webhook configurado"
                    : "Sem push externo"
              }
            />
          </StatsMiniKpiRow>

          {data.open_alerts.length > 0 ? (
            <ul className="admin-stats-console-alerts">
              {data.open_alerts.slice(0, 3).map((alert) => (
                <li key={`${alert.code}-${alert.message}`}>
                  <span className={`admin-stats-console-alerts__sev admin-stats-console-alerts__sev--${alert.severity}`}>
                    {alert.severity}
                  </span>
                  <span>{alert.message}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="admin-stats__empty">Nenhum alerta aberto no momento.</p>
          )}
        </>
      ) : null}
    </section>
  );
}
