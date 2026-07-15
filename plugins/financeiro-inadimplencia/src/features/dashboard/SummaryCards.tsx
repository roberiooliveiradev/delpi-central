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

  const heroToneClass =
    comparison.trend === "melhor"
      ? " fi-kpi-hero__delta--up"
      : comparison.trend === "pior"
        ? " fi-kpi-hero__delta--down"
        : "";

  const topClienteNome = topClienteMes?.nome_reduzido?.trim() || "—";
  const topClienteSubtitle = topClienteMes
    ? `${topClienteMes.cliente_codigo}/${topClienteMes.loja} · ${formatInteger(topClienteMes.titulos_atraso)} atrasado(s) · ${formatCurrencyBrl(topClienteMes.valor_atraso)}`
    : loading
      ? "Buscando ranking do mês…"
      : "Nenhum cliente com atraso no mês atual";

  return (
    <div className="fi-kpi-grid" aria-label="Indicadores principais">
      {/* Domínio: hero composto (não é SimpleKpi do kit). */}
      <section className="fi-card fi-kpi-hero" aria-label="Pontualidade do mês atual">
        <div className="fi-kpi-hero__head">
          <span className="fi-kpi-hero__icon" aria-hidden="true">
            <BadgeCheck size={22} />
          </span>
          <div>
            <p className="fi-kpi-hero__eyebrow">Pontualidade por quantidade</p>
            <p className="fi-kpi-hero__month">Mês atual · {currentLabel}</p>
          </div>
        </div>

        <p className="fi-kpi-hero__value">
          {loading ? "…" : formatPercent(current?.percentual_em_dia_qtd)}
        </p>

        <p className={`fi-kpi-hero__delta${heroToneClass}`}>
          {loading ? "Comparando…" : deltaText}
        </p>

        <p className="fi-kpi-hero__meta">
          {loading
            ? "Carregando…"
            : current
              ? `${formatInteger(current.titulos_em_dia)} de ${formatInteger(current.total_titulos)} títulos pagos em dia`
              : "Sem dados do mês atual no período."}
        </p>
      </section>

      <KpiCard
        title="Inadimplência do mês"
        value={formatPercent(
          current
            ? Math.max(0, 100 - current.percentual_em_dia_qtd)
            : null,
        )}
        subtitle={
          current
            ? `${formatInteger(current.titulos_atraso)} títulos pagos após o vencimento`
            : "Sem dados do mês atual"
        }
        icon={<TimerOff size={20} aria-hidden="true" />}
        loading={loading}
        valueTone="danger"
      />

      <KpiCard
        title="Valor pago com atraso"
        value={formatCurrencyBrl(current?.valor_atraso)}
        subtitle={
          current
            ? `Referente a ${currentLabel}`
            : "Sem dados do mês atual"
        }
        icon={<AlertTriangle size={20} aria-hidden="true" />}
        loading={loading}
        valueTone="danger"
      />

      {/* Domínio: card clicável do ranking (não dual-class parcial do kit). */}
      <button
        type="button"
        className="fi-card fi-kpi-hero fi-kpi-hero--clickable fi-kpi-hero--danger"
        onClick={onOpenTopClientes}
        disabled={!onOpenTopClientes || loading}
        aria-label="Abrir ranking de clientes inadimplentes do mês"
      >
        <div className="fi-kpi-hero__head">
          <span className="fi-kpi-hero__icon fi-kpi-hero__icon--danger" aria-hidden="true">
            <UserRoundX size={20} />
          </span>
          <p className="fi-kpi-hero__eyebrow">Cliente mais inadimplente</p>
        </div>
        <p className="fi-kpi-hero__value fi-kpi-hero__value--danger">
          {loading ? "…" : topClienteNome}
        </p>
        <p className="fi-kpi-hero__meta">{topClienteSubtitle}</p>
        <p className="fi-kpi-hero__cta">Clique para ver o ranking do mês</p>
      </button>
    </div>
  );
}
