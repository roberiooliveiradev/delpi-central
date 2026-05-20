import { Sheet } from "lucide-react";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <article className="ds-source-banner">
        <Sheet size={18} aria-hidden="true" />
        <div>
          <strong>Planilha Google Sheets — TRANSFORMA+ DELPI</strong>
          <p>
            Ganhos financeiros, horas economizadas e processos de melhoria vêm do
            preenchimento da planilha do Transforma+ (processos, revisões e
            medições).
          </p>
        </div>
      </article>
    </div>
  );
}
