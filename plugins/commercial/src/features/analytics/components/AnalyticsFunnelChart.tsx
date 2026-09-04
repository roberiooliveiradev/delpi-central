import { useMemo, type CSSProperties } from "react";
import { EmptyState, runTabularExport } from "@delpi/plugin-ui/index";

import {
  cmEmptyStateClassNames,
  CommercialTabularExportButtons,
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { buildOverviewFunnelPayload } from "../../overview/overviewExportBuilders";
import type { ClosingRateData } from "../../../types/analytics";
import { formatNumber } from "../../../utils/format";
import { resolveLevelUnitGoalValue } from "../../overview/goalDisplay";

type AnalyticsFunnelChartProps = {
  closingRate: ClosingRateData | null;
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

function formatPercent(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${formatNumber(value, digits)}%`;
}

function formatInteger(value: number): string {
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

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

/**
 * Funil trapézio — padrão dashboard-commercial (taxa/meta + 3 etapas).
 */
export function AnalyticsFunnelChart({
  closingRate,
  loading = false,
}: AnalyticsFunnelChartProps) {
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;
  const proposals = closingRate?.qtd_proposals ?? 0;
  const won = closingRate?.qtd_won ?? 0;
  const conversionPct = closingRate?.sales_conversion_rate_pct ?? null;
  const goalPct = resolveLevelUnitGoalValue(closingRate);

  const stages = useMemo(() => buildStages(proposals, won), [proposals, won]);
  const hasData = proposals > 0;

  if (loading && !hasData) {
    return (
      <div className="cm-funnel cm-funnel--loading" aria-busy="true">
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage="Carregando funil…" />
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="cm-funnel cm-funnel--empty">
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={emptyCopy.funnelTitle}
          defaultMessage={emptyCopy.funnelMessage}
        />
      </div>
    );
  }

  const gapToGoal =
    goalPct != null && conversionPct != null ? conversionPct - goalPct : null;

  return (
    <div className="cm-funnel" role="img" aria-label="Funil de conversão comercial">
      <div className="cm-funnel__summary">
        <div className="cm-funnel__export">
          <CommercialTabularExportButtons
            compact
            disabled={loading}
            onExport={(format) => {
              runTabularExport({
                kind: "table",
                format,
                payload: buildOverviewFunnelPayload(closingRate),
              });
            }}
          />
        </div>
        <div className="cm-funnel__rate">
          <span className="cm-funnel__rate-label">Taxa de conversão</span>
          <strong className="cm-funnel__rate-value">{formatPercent(conversionPct)}</strong>
          <span className="cm-funnel__rate-detail">
            {formatInteger(won)} de {formatInteger(proposals)} propostas
          </span>
        </div>

        {goalPct != null ? (
          <div className="cm-funnel__goal">
            <span className="cm-funnel__goal-label">Meta do período</span>
            <strong>{formatPercent(goalPct)}</strong>
            {gapToGoal != null ? (
              <span
                className={
                  gapToGoal >= 0
                    ? "cm-funnel__goal-gap cm-funnel__goal-gap--ok"
                    : "cm-funnel__goal-gap cm-funnel__goal-gap--below"
                }
              >
                {gapToGoal >= 0 ? "+" : ""}
                {formatPercent(gapToGoal, 2)} vs meta
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="cm-funnel__visual">
        <div className="cm-funnel__stages">
          {stages.map((stage, index) => (
            <div key={stage.key} className="cm-funnel__stage-wrap">
              {index > 0 ? (
                <div className="cm-funnel__arrow" aria-hidden="true">
                  <span className="cm-funnel__arrow-line" />
                  {index === 1 ? (
                    <span className="cm-funnel__arrow-label">
                      {formatPercent(stage.sharePct, 1)} convertidas
                    </span>
                  ) : null}
                </div>
              ) : null}

              <div
                className={`cm-funnel__stage cm-funnel__stage--${stage.tone}`}
                style={
                  {
                    "--cm-funnel-width": `${stage.widthPct}%`,
                    "--cm-funnel-accent":
                      stage.tone === "won"
                        ? "var(--cm-success, #15803d)"
                        : stage.tone === "lost"
                          ? "var(--cm-danger, #b91c1c)"
                          : "var(--cm-accent, #089bdb)",
                  } as CSSProperties
                }
              >
                <div className="cm-funnel__stage-inner">
                  <span className="cm-funnel__stage-value">{formatInteger(stage.value)}</span>
                  <span className="cm-funnel__stage-label">{stage.label}</span>
                  <span className="cm-funnel__stage-share">
                    {formatPercent(stage.sharePct, 1)} do total
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        <p className="cm-funnel__footnote">{ANALYTICS_CONTENT.overview.funnelFootnote}</p>
      </div>
    </div>
  );
}
