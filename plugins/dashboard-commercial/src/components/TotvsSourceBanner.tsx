import { Database } from "lucide-react";

export function TotvsSourceBanner() {
  return (
    <div className="dc-totvs-banner dc-no-print" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong>Origem: TOTVS Protheus</strong>
        <p>
          ROL por unidade (filiais 01 e 02), taxa de conversão, OTD e novos
          negócios — metas do Indicadores Estratégicos.
        </p>
      </div>
    </div>
  );
}
