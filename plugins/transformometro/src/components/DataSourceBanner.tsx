import { Database } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <article className="ds-source-banner">
        <Database size={18} aria-hidden="true" />
        <div>
          <strong>PostgreSQL — Transformômetro</strong>
          <p>
            Cadastro e cálculos materializados em <code>dashboard_calculos</code>.
            Use <strong>Recalcular</strong> após alterar medições, investimentos ou vínculos.
          </p>
        </div>
      </article>
    </div>
  );
}
