import { Database, Sheet } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="dp-source-banners" role="note">
      <article className="dp-source-banner">
        <Sheet size={18} aria-hidden="true" />
        <div>
          <strong>Planilhas Google</strong>
          <p>
            MO direta, custo de produção e depreciação (% sobre ROL do período).
          </p>
        </div>
      </article>
      <article className="dp-source-banner">
        <Database size={18} aria-hidden="true" />
        <div>
          <strong>TOTVS Protheus</strong>
          <p>
            OEE (apontamentos SH6010) e OTD (ordens SC2010) no intervalo
            filtrado.
          </p>
        </div>
      </article>
    </div>
  );
}
