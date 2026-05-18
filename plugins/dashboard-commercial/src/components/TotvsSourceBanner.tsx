import { Database } from "lucide-react";

export function TotvsSourceBanner() {
  return (
    <div className="dc-totvs-banner dc-no-print" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong>Origem: TOTVS Protheus</strong>
        <p>
          Metas de ROL (matriz 01 e filial 02), conversão de vendas e indicadores
          de clientes novos.
        </p>
      </div>
    </div>
  );
}
