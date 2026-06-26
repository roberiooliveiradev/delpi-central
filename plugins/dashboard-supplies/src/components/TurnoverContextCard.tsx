import { Database } from "lucide-react";

import type { InventoryTurnoverData } from "../types/supplies";
import {
  formatPeriodLabelLong,
  humanizeProtheusDatesInText,
} from "../utils/dates";
import { formatCurrency, formatDecimal } from "../utils/format";
import {
  buildStockEstimationStats,
  methodBadge,
  type ContextStat,
} from "./stockContextHelpers";

type TurnoverContextCardProps = {
  dateStart?: string;
  dateEnd?: string;
  branchLabel: string;
  locationLabel: string;
  data?: InventoryTurnoverData | null;
  isOfficialClosure: boolean;
  isRegisterSnapshot: boolean;
};

const CALC_MODE_LABEL: Record<string, string> = {
  closed_month: "Mês fechado",
  full_month_range: "Intervalo de meses completos",
  partial_period_monthlyized: "Período parcial (mensalizado)",
};

function buildTurnoverStats(data: InventoryTurnoverData): ContextStat[] {
  const mode = data.calculation_context.calculation_mode;
  return [
    {
      label: "Giro (vezes)",
      value: formatDecimal(data.summary.inventory_turnover_times, 2),
      hint: "CPV total ÷ estoque",
    },
    {
      label: "Giro (meses)",
      value: formatDecimal(data.summary.inventory_turnover_months, 2),
      hint: "Estoque ÷ CPV médio mensal",
    },
    {
      label: "Estoque no cálculo",
      value: formatCurrency(data.summary.total_stock_value),
    },
    {
      label: "CPV médio mensal",
      value: formatCurrency(data.summary.cpv_average_monthly),
      hint: CALC_MODE_LABEL[mode] ?? mode,
    },
    {
      label: "CPV total no período",
      value: formatCurrency(data.summary.cpv_total),
    },
    {
      label: "Referência (meses)",
      value: String(data.calculation_context.period_reference ?? "—"),
    },
  ];
}

export function TurnoverContextCard({
  dateStart,
  dateEnd,
  branchLabel,
  locationLabel,
  data,
  isOfficialClosure,
  isRegisterSnapshot,
}: TurnoverContextCardProps) {
  const estimation = data?.stock_estimation;
  const stockBadge = methodBadge(isOfficialClosure, isRegisterSnapshot, estimation);
  const periodValid = data?.calculation_context.idd_period_valid ?? true;
  const calcMode = data?.calculation_context.calculation_mode;
  const calcLabel =
    (calcMode && CALC_MODE_LABEL[calcMode]) || stockBadge.label;

  const periodLabel = formatPeriodLabelLong(dateStart, dateEnd);
  const turnoverStats = data ? buildTurnoverStats(data) : [];
  const stockStats = buildStockEstimationStats(estimation, isRegisterSnapshot);

  const note = estimation?.note
    ? humanizeProtheusDatesInText(estimation.note)
    : null;
  const warning = estimation?.data_quality_warning
    ? humanizeProtheusDatesInText(estimation.data_quality_warning)
    : null;

  const periodWarning =
    data && !periodValid
      ? "Período parcial para o cálculo oficial do giro. O CPV é mensalizado; prefira mês fechado ou intervalo só com meses completos."
      : null;

  return (
    <article className="ds-card ds-stock-context-card" aria-label="Contexto do giro de estoque">
      <header className="ds-stock-context-card__header">
        <div className="ds-stock-context-card__brand" aria-hidden="true">
          <Database size={22} />
        </div>
        <div className="ds-stock-context-card__intro">
          <h2 className="ds-stock-context-card__title">TOTVS Protheus</h2>
          <p className="ds-stock-context-card__sources">
            Saldo de estoque e CPV (SD3) no período — base do giro em vezes e em meses.
          </p>
        </div>
        <span
          className={`ds-stock-context-card__badge ds-stock-context-card__badge--${
            periodValid ? stockBadge.tone : "neutral"
          }`}
        >
          {calcLabel}
        </span>
      </header>

      <dl className="ds-stock-context-card__meta">
        <div>
          <dt>Período</dt>
          <dd>{periodLabel}</dd>
        </div>
        <div>
          <dt>Escopo</dt>
          <dd>
            {branchLabel} · {locationLabel}
          </dd>
        </div>
        <div>
          <dt>Período válido</dt>
          <dd>{periodValid ? "Sim" : "Parcial (mensalizado)"}</dd>
        </div>
      </dl>

      <div className="ds-stock-context-card__body">
        {periodWarning ? (
          <p className="ds-stock-context-card__warning" role="alert">
            {periodWarning}
          </p>
        ) : null}
        {note ? <p className="ds-stock-context-card__note">{note}</p> : null}
        {warning ? (
          <p className="ds-stock-context-card__warning" role="alert">
            {warning}
          </p>
        ) : null}

        {turnoverStats.length > 0 ? (
          <div className="ds-stock-context-card__composition">
            <h3 className="ds-stock-context-card__composition-title">
              Composição do giro de estoque
            </h3>
            <div className="ds-stock-context-card__stats">
              {turnoverStats.map((stat) => (
                <div key={stat.label} className="ds-stock-context-card__stat">
                  <span className="ds-stock-context-card__stat-label">{stat.label}</span>
                  <strong className="ds-stock-context-card__stat-value">{stat.value}</strong>
                  {stat.hint ? (
                    <span className="ds-stock-context-card__stat-hint">{stat.hint}</span>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {stockStats.length > 0 ? (
          <div className="ds-stock-context-card__composition">
            <h3 className="ds-stock-context-card__composition-title">
              {isRegisterSnapshot
                ? "Composição do inventário (proxy MATR460)"
                : "Base de estoque no cálculo"}
            </h3>
            <div className="ds-stock-context-card__stats">
              {stockStats.map((stat) => (
                <div key={stat.label} className="ds-stock-context-card__stat">
                  <span className="ds-stock-context-card__stat-label">{stat.label}</span>
                  <strong className="ds-stock-context-card__stat-value">{stat.value}</strong>
                  {stat.hint ? (
                    <span className="ds-stock-context-card__stat-hint">{stat.hint}</span>
                  ) : null}
                </div>
              ))}
            </div>
            {isRegisterSnapshot ? (
              <p className="ds-stock-context-card__footnote">
                O valor de estoque usado no giro corresponde ao{" "}
                <strong>EM estoque (SB2)</strong>, alinhado ao Registro de Inventário.
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}
