import { CircleDollarSign, ClipboardList, Package, TriangleAlert } from "lucide-react";

import type { ScrapResumo } from "../types/scrap";
import { formatCurrencyBrl, formatInteger, formatQuantity } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  resumo: ScrapResumo | null;
  loading?: boolean;
};

export function SummaryCards({ resumo, loading = false }: SummaryCardsProps) {
  return (
    <div className="sm-kpi-grid">
      <KpiCard
        title="R$ Refugo dia"
        value={formatCurrencyBrl(resumo?.valorDia)}
        icon={<CircleDollarSign size={22} />}
        loading={loading}
      />
      <KpiCard
        title="R$ Refugo no mês"
        value={formatCurrencyBrl(resumo?.valorMes)}
        icon={<CircleDollarSign size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Total no período"
        value={formatCurrencyBrl(resumo?.totalValor)}
        icon={<Package size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Ocorrências"
        value={formatInteger(resumo?.ocorrencias)}
        icon={<ClipboardList size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Quantidade"
        value={formatQuantity(resumo?.totalQuantidade)}
        icon={<Package size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Sem custo"
        value={formatInteger(resumo?.registrosSemCusto)}
        icon={<TriangleAlert size={22} />}
        loading={loading}
      />
    </div>
  );
}
