import {
  Building2,
  CircleDollarSign,
  Receipt,
  Store,
  TrendingUp,
  Users,
} from "lucide-react";

import type { DespesasResumoData } from "../types/despesasCentroCusto";
import { formatCurrencyBrl, formatInteger } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  resumo: DespesasResumoData | null;
  loading?: boolean;
};

export function SummaryCards({ resumo, loading = false }: SummaryCardsProps) {
  return (
    <div className="fcc-kpi-grid">
      <KpiCard
        title="Total do período"
        value={formatCurrencyBrl(resumo?.total_periodo)}
        icon={<CircleDollarSign size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Quantidade de lançamentos"
        value={formatInteger(resumo?.quantidade_lancamentos)}
        icon={<Receipt size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Centros de custo"
        value={formatInteger(resumo?.quantidade_centros_custo)}
        icon={<Building2 size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Fornecedores"
        value={formatInteger(resumo?.quantidade_fornecedores)}
        icon={<Users size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Ticket médio"
        value={formatCurrencyBrl(resumo?.ticket_medio)}
        icon={<TrendingUp size={20} />}
        loading={loading}
      />
      <KpiCard
        title="Maior lançamento"
        value={formatCurrencyBrl(resumo?.maior_lancamento)}
        icon={<Store size={20} />}
        loading={loading}
      />
    </div>
  );
}
