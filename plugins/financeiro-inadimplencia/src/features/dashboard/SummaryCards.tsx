import { AlertTriangle, BadgeCheck, TimerOff, UserRoundX } from "lucide-react";

import type {
  InadimplenciaClienteItem,
  InadimplenciaMensalData,
} from "../../types/inadimplencia";
import {
  formatCurrencyBrl,
  formatInteger,
  formatMonthYearPtBr,
  formatPercent,
} from "../../utils/formatters";
import {
  comparePontualidadeQtd,
  resolveMonthComparison,
} from "../../utils/monthComparison";
import { KpiCard } from "../../components/KpiCard";

type SummaryCardsProps = {
  mensal: InadimplenciaMensalData | null;
  topClienteMes?: InadimplenciaClienteItem | null;
  loading?: boolean;
  onOpenTopClientes?: () => void;
};

const deltaFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "always",
});

export function SummaryCards({
  mensal,
  topClienteMes = null,
  loading = false,
  onOpenTopClientes,
}: SummaryCardsProps) {
  const { current, previous } = resolveMonthComparison(mensal?.items ?? []);
  const comparison = comparePontualidadeQtd(
    current?.percentual_em_dia_qtd,
    previous?.percentual_em_dia_qtd,
  );

  const currentLabel = formatMonthYearPtBr(current?.ano_mes || current?.mes);
  const previousLabel = formatMonthYearPtBr(previous?.ano_mes || previous?.mes);

  let deltaText = "Sem mês anterior para comparar.";
  if (comparison.trend === "estavel" && previous) {
    deltaText = `Estável vs ${previousLabel} (0,00%)`;
  } else if (comparison.deltaPp != null && previous) {
    const trendLabel =
      comparison.trend === "melhor"
        ? "melhor"
        : comparison.trend === "pior"
          ? "pior"
          : "estável";
    deltaText = `${deltaFormatter.format(comparison.deltaPp)}% vs ${previousLabel} — ${trendLabel}`;
  }

  const pontualidadeMeta = current
    ? `${formatInteger(current.titulos_em_dia)} de ${formatInteger(current.total_titulos)} títulos pagos em dia`
    : "Sem dados do mês atual no período.";

  const topClienteNome = topClienteMes?.nome_reduzido?.trim() || "—";
  const topClienteSubtitle = topClienteMes
    ? `${topClienteMes.cliente_codigo}/${topClienteMes.loja} · ${formatInteger(topClienteMes.titulos_atraso)} atrasado(s) · ${formatCurrencyBrl(topClienteMes.valor_atraso)} · Clique para ver o ranking do mês`
    : loading
      ? "Buscando ranking do mês…"
      : "Nenhum cliente com atraso no mês atual";

  const topClienteCard = (
    <KpiCard
      title="Cliente mais inadimplente"
      value={loading ? "…" : topClienteNome}
      subtitle={topClienteSubtitle}
      icon={<UserRoundX size={20} aria-hidden="true" />}
      loading={loading}
      valueTone="danger"
      iconTone="danger"
    />
  );

  return (
    <div className="fi-kpi-grid" aria-label="Indicadores principais">
      <KpiCard
        title="Pontualidade por quantidade"
        value={formatPercent(current?.percentual_em_dia_qtd)}
        subtitle={
          loading
            ? "Comparando…"
            : `Mês atual · ${currentLabel} · ${deltaText} · ${pontualidadeMeta}`
        }
        icon={<BadgeCheck size={20} aria-hidden="true" />}
        loading={loading}
        iconTone={
          comparison.trend === "melhor"
            ? "success"
            : comparison.trend === "pior"
              ? "danger"
              : undefined
        }
      />

      <KpiCard
        title="Inadimplência do mês"
        value={formatPercent(
          current ? Math.max(0, 100 - current.percentual_em_dia_qtd) : null,
        )}
        subtitle={
          current
            ? `${formatInteger(current.titulos_atraso)} títulos pagos após o vencimento`
            : "Sem dados do mês atual"
        }
        icon={<TimerOff size={20} aria-hidden="true" />}
        loading={loading}
        valueTone="danger"
        iconTone="danger"
      />

      <KpiCard
        title="Valor pago com atraso"
        value={formatCurrencyBrl(current?.valor_atraso)}
        subtitle={current ? `Referente a ${currentLabel}` : "Sem dados do mês atual"}
        icon={<AlertTriangle size={20} aria-hidden="true" />}
        loading={loading}
        valueTone="danger"
        iconTone="warning"
      />

      {onOpenTopClientes ? (
        <button
          type="button"
          className="fi-kpi-as-button"
          onClick={onOpenTopClientes}
          disabled={loading}
          aria-label="Abrir ranking de clientes inadimplentes do mês"
        >
          {topClienteCard}
        </button>
      ) : (
        topClienteCard
      )}
    </div>
  );
}
