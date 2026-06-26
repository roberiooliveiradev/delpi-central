import { useMemo, type CSSProperties } from "react";

import { CHART_COLORS } from "../constants/chartColors";
import { formatInteger, formatPercent } from "../utils/format";
import type { ClosingRateData } from "../types/commercial";

type ConversionFunnelChartProps = {
  data: ClosingRateData | null;
  loading?: boolean;
};

type FunnelStage = {
  key: string;
  label: string;
  value: number;
  sharePct: number;
  widthPct: number;
  tone: "proposals" | "won" | "lost";
};

function buildStages(proposals: number, won: number): FunnelStage[] {
  const lost = Math.max(proposals - won, 0);
  const wonShare = proposals > 0 ? (won / proposals) * 100 : 0;
  const lostShare = proposals > 0 ? (lost / proposals) * 100 : 0;

  return [
    {
      key: "proposals",
      label: "Propostas no período",
      value: proposals,
      sharePct: 100,
      widthPct: 100,
      tone: "proposals",
    },
    {
      key: "won",
      label: "Ganhas (aceite no período)",
      value: won,
      sharePct: wonShare,
      widthPct: proposals > 0 ? Math.max(32, Math.min(100, wonShare)) : 0,
      tone: "won",
    },
    {
      key: "lost",
      label: "Sem conversão",
      value: lost,
      sharePct: lostShare,
      widthPct: proposals > 0 ? Math.max(40, Math.min(100, lostShare)) : 0,
      tone: "lost",
    },
  ];
}

export function ConversionFunnelChart({
  data,
  loading = false,
}: ConversionFunnelChartProps) {
  const proposals = data?.qtd_proposals ?? 0;
  const won = data?.qtd_won ?? 0;
  const conversionPct = data?.sales_conversion_rate_pct ?? null;
  const goalPct = data?.comparable_goal ?? data?.target ?? null;

  const stages = useMemo(
    () => buildStages(proposals, won),
    [proposals, won],
  );

  const hasData = proposals > 0;

  if (loading && !hasData) {
    return (
      <div className="dc-funnel dc-funnel--loading" aria-busy="true">
        <div className="dc-state-box">Carregando funil…</div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="dc-funnel dc-funnel--empty">
        <div className="dc-state-box">Sem propostas no período filtrado.</div>
      </div>
    );
  }

  const gapToGoal =
    goalPct != null && conversionPct != null ? conversionPct - goalPct : null;

  return (
    <div className="dc-funnel" role="img" aria-label="Funil de conversão comercial">
      <div className="dc-funnel__summary">
        <div className="dc-funnel__rate">
          <span className="dc-funnel__rate-label">Taxa de conversão</span>
          <strong className="dc-funnel__rate-value">
            {formatPercent(conversionPct)}
          </strong>
          <span className="dc-funnel__rate-detail">
            {formatInteger(won)} de {formatInteger(proposals)} propostas
          </span>
        </div>

        {goalPct != null ? (
          <div className="dc-funnel__goal">
            <span className="dc-funnel__goal-label">Meta do período</span>
            <strong>{formatPercent(goalPct)}</strong>
            {gapToGoal != null ? (
              <span
                className={
                  gapToGoal >= 0
                    ? "dc-funnel__goal-gap dc-funnel__goal-gap--ok"
                    : "dc-funnel__goal-gap dc-funnel__goal-gap--below"
                }
              >
                {gapToGoal >= 0 ? "+" : ""}
                {formatPercent(gapToGoal, 2)} vs meta
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="dc-funnel__visual">
        <div className="dc-funnel__stages">
          {stages.map((stage, index) => (
            <div key={stage.key} className="dc-funnel__stage-wrap">
              {index > 0 ? (
                <div className="dc-funnel__arrow" aria-hidden="true">
                  <span className="dc-funnel__arrow-line" />
                  {index === 1 ? (
                    <span className="dc-funnel__arrow-label">
                      {formatPercent(stage.sharePct, 1)} convertidas
                    </span>
                  ) : null}
                </div>
              ) : null}

              <div
                className={`dc-funnel__stage dc-funnel__stage--${stage.tone}`}
                style={
                  {
                    "--dc-funnel-width": `${stage.widthPct}%`,
                    "--dc-funnel-accent":
                      stage.tone === "won"
                        ? CHART_COLORS[4]
                        : stage.tone === "lost"
                          ? "#e85d4c"
                          : CHART_COLORS[0],
                  } as CSSProperties
                }
              >
                <div className="dc-funnel__stage-inner">
                  <span className="dc-funnel__stage-value">
                    {formatInteger(stage.value)}
                  </span>
                  <span className="dc-funnel__stage-label">{stage.label}</span>
                  <span className="dc-funnel__stage-share">
                    {formatPercent(stage.sharePct, 1)} do total
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="dc-funnel__footnote">
          Largura das etapas proporcional ao volume; números absolutos em cada
          faixa. Ganhas = propostas com status TOTVS <code>9</code> e aceite (
          <code>AD1_DTASSI</code>) no período filtrado.
        </p>
      </div>
    </div>
  );
}
