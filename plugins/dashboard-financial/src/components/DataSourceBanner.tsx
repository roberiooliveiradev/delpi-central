import { Database, Sheet } from "lucide-react";

type DataSourceBannerProps = {
  /** Exibe só a origem TOTVS (ex.: aba ROL). */
  variant?: "all" | "totvs" | "sheets";
};

export function DataSourceBanner({ variant = "all" }: DataSourceBannerProps) {
  const showTotvs = variant === "all" || variant === "totvs";
  const showSheets = variant === "all" || variant === "sheets";

  return (
    <div className="ds-source-banners" role="note">
      {showSheets ? (
        <article className="ds-source-banner">
          <Sheet size={18} aria-hidden="true" />
          <div>
            <strong>Planilha Google Sheets</strong>
            <p>
              EBITDA, custos fixos e prazo médio de recebimento vêm do
              preenchimento manual da planilha (médias por filial no período
              filtrado).
            </p>
          </div>
        </article>
      ) : null}
      {showTotvs ? (
        <article className="ds-source-banner">
          <Database size={18} aria-hidden="true" />
          <div>
            <strong>TOTVS Protheus</strong>
            <p>ROL (faturamento SD2/F2) calculada no período filtrado.</p>
          </div>
        </article>
      ) : null}
    </div>
  );
}
