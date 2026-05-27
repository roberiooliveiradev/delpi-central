import { Database } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <article className="ds-source-banner">
        <Database size={18} aria-hidden="true" />
        <div>
          <strong>PostgreSQL — Transformômetro</strong>
          <p>
            KPIs e gráficos são calculados em tempo real a partir do cadastro (revisões, medições,
            investimentos e recursos), respeitando vigências e competências de cada mês.
          </p>
        </div>
      </article>
    </div>
  );
}
