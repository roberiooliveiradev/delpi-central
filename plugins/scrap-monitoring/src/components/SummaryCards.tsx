import { CircleDollarSign, ClipboardList, Package, TriangleAlert } from "lucide-react";

import { SCRAP_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { ScrapResumo } from "../types/scrap";
import { formatCurrencyBrl, formatInteger, formatQuantity } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  resumo: ScrapResumo | null;
  loading?: boolean;
};

const H = SCRAP_HELP_TOOLTIPS.kpis;

export function SummaryCards({ resumo, loading = false }: SummaryCardsProps) {
  return (
    <div className="sm-kpi-grid">
      <KpiCard
        title="R$ Refugo dia"
        titleHint={H.valorDia}
        value={formatCurrencyBrl(resumo?.valorDia)}
        icon={<CircleDollarSign size={22} />}
        loading={loading}
      />
      <KpiCard
        title="R$ Refugo no mês"
        titleHint={H.valorMes}
        value={formatCurrencyBrl(resumo?.valorMes)}
        icon={<CircleDollarSign size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Sem custo"
        titleHint={H.semCusto}
        value={formatInteger(resumo?.registrosSemCusto)}
        icon={<TriangleAlert size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Ocorrências"
        titleHint={H.ocorrencias}
        value={formatInteger(resumo?.ocorrencias)}
        icon={<ClipboardList size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Quantidade"
        titleHint={H.quantidade}
        value={formatQuantity(resumo?.totalQuantidade)}
        icon={<Package size={22} />}
        loading={loading}
      />
      <KpiCard
        title="Total no período"
        titleHint={H.totalPeriodo}
        value={formatCurrencyBrl(resumo?.totalValor)}
        icon={<Package size={22} />}
        loading={loading}
      />
    </div>
  );
}
