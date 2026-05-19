import { Database } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <article className="ds-source-banner">
        <Database size={18} aria-hidden="true" />
        <div>
          <strong>TOTVS Protheus</strong>
          <p>
            ROL (faturamento SD2/F2), EBITDA, custos fixos e prazo médio de
            recebimento no período filtrado.
          </p>
        </div>
      </article>
    </div>
  );
}
