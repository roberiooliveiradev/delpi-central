import { Database } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <article className="ds-source-banner">
        <Database size={18} aria-hidden="true" />
        <div>
          <strong>TOTVS Protheus</strong>
          <p>
            CPV (movimentos SD3), OTD de linhas de compras, saldo de estoque e
            base para o giro IDD no período filtrado.
          </p>
        </div>
      </article>
    </div>
  );
}
