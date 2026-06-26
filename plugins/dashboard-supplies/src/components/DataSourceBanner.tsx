import { Database } from "lucide-react";

import { InfoCard } from "./InfoCard";

export function DataSourceBanner() {
  return (
    <div className="ds-source-banners" role="note">
      <InfoCard variant="info" icon={<Database size={18} />} title="TOTVS Protheus">
        CPV (movimentos SD3), OTD de linhas de compras, saldo de estoque e base
        para o giro de estoque no período filtrado. Economia em negociações vem
        da planilha IDD Suprimentos (Google Sheets).
      </InfoCard>
    </div>
  );
}
