import { Database } from "lucide-react";

export function TotvsSourceBanner() {
  return (
    <div className="dc-totvs-banner dc-no-print" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong>Origem: TOTVS Protheus</strong>
        <p>
          ROL em reais (matriz 01 e filial 02), taxa de conversão de vendas e
          indicadores de clientes novos.
        </p>
      </div>
    </div>
  );
}
