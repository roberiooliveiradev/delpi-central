import type { AdminQualityUnifiedSummary } from "../../../../data/api/adminTypes";

type AdminQualityUnifiedMetricsProps = {
  summary: AdminQualityUnifiedSummary | null;
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

export function AdminQualityUnifiedMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminQualityUnifiedMetricsProps) {
  const health = summary?.health;
  const adoption = summary?.adoption;
  const efficiency = summary?.efficiency;
  const security = summary?.security;

  return (
    <section className="mdc-admin-drawing-metrics" aria-labelledby="mdc-admin-quality-unified-title">
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 10</p>
          <h3 id="mdc-admin-quality-unified-title">Qualidade unificada</h3>
          <p>
            Feedback, adoção, eficiência e segurança consolidados na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? <p className="mdc-chat-muted">Carregando visão unificada...</p> : null}

      {summary ? (
        <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
          <article className="mdc-admin-kpi-card">
            <h4>CSAT</h4>
            <strong>{formatPercent(health?.csat)}</strong>
          </article>
          <article className="mdc-admin-kpi-card">
            <h4>Usuários ativos</h4>
            <strong>{formatNumber(adoption?.activeUsers)}</strong>
          </article>
          <article className="mdc-admin-kpi-card">
            <h4>Mensagens / sessão</h4>
            <strong>{formatNumber(efficiency?.messagesPerSession)}</strong>
          </article>
          <article className="mdc-admin-kpi-card">
            <h4>Latência média</h4>
            <strong>{formatNumber(efficiency?.latencyAvgMs)} ms</strong>
          </article>
          <article className="mdc-admin-kpi-card">
            <h4>CTR chips</h4>
            <strong>{formatPercent(adoption?.chipClickRate)}</strong>
          </article>
          <article className="mdc-admin-kpi-card">
            <h4>Bloqueios segurança</h4>
            <strong>{formatNumber(security?.blockedCount)}</strong>
          </article>
        </div>
      ) : null}
    </section>
  );
}
