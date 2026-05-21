import { Database } from "lucide-react";

type DataSourceBannerProps = {
  variant?: "all" | "lmp" | "transforma";
};

export function DataSourceBanner({ variant = "all" }: DataSourceBannerProps) {
  const showLmp = variant === "all" || variant === "lmp";
  const showTransforma = variant === "all" || variant === "transforma";

  return (
    <div className="ds-source-banners" role="note">
      {showLmp ? (
        <article className="ds-source-banner">
          <Database size={18} aria-hidden="true" />
          <div>
            <strong>TOTVS Protheus</strong>
            <p>
              LMPs, amostras e propostas — % no prazo e lead time calculados a
              partir dos apontamentos de engenharia (SH6010).
            </p>
          </div>
        </article>
      ) : null}
      {showTransforma ? (
        <article className="ds-source-banner">
          <Database size={18} aria-hidden="true" />
          <div>
            <strong>API Transformômetro</strong>
            <p>
              Ganhos, ROI e processos via <code>transformometro-api</code> (cadastro
              oficial no Postgres). Rotas de engenharia fazem proxy para essa API.
            </p>
          </div>
        </article>
      ) : null}
    </div>
  );
}
