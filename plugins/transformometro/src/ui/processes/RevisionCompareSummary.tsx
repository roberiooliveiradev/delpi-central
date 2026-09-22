import { HelpTooltip } from "@delpi/plugin-ui/index";

import { TmStatusBadge } from "../../components/tmChromeUi";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { formatProcessoNumber } from "../../utils/processoDetailTables";
import {
  provenanceLabelText,
  type ProvenanceLabel,
} from "./buildRevisionComparisonView";

const H = TM_HELP_TOOLTIPS.resultados;

type Props = {
  asIsLabel: string;
  toBeLabel: string | null;
  asIsProvenance: ProvenanceLabel;
  toBeProvenance: ProvenanceLabel | null;
  mode: "baseline_only" | "pair" | "blocked";
  /** Optional calculated highlight from comparison contract (not measurement). */
  calculatedSummary?: {
    asIsEconomy: number | null;
    toBeEconomy: number | null;
    deltaEconomy: number | null;
  };
};

/**
 * Visual AS-IS × TO-BE × DELTA summary — labels textuais, não só cor.
 */
export function RevisionCompareSummary({
  asIsLabel,
  toBeLabel,
  asIsProvenance,
  toBeProvenance,
  mode,
  calculatedSummary,
}: Props) {
  return (
    <div
      className="tm-revision-compare-summary"
      role="group"
      aria-label="Comparação AS-IS, TO-BE e Delta"
    >
      <article
        className="tm-revision-compare-summary__card tm-revision-compare-summary__card--asis"
        aria-labelledby="tm-cmp-asis-title"
      >
        <div className="tm-revision-compare-summary__role-row">
          <h4 id="tm-cmp-asis-title" className="tm-revision-compare-summary__role">
            AS-IS
          </h4>
          <HelpTooltip content={H.asIs} ariaLabel="Ajuda: AS-IS" />
        </div>
        <p className="tm-revision-compare-summary__helper">Referência atual</p>
        <p className="tm-revision-compare-summary__value">{asIsLabel}</p>
        <TmStatusBadge label={provenanceLabelText(asIsProvenance)} variant="neutral" />
        {calculatedSummary?.asIsEconomy != null ? (
          <p className="tm-revision-compare-summary__metric">
            Economia líquida/mês: {formatProcessoNumber(calculatedSummary.asIsEconomy)}
          </p>
        ) : null}
      </article>

      <article
        className="tm-revision-compare-summary__card tm-revision-compare-summary__card--tobe"
        aria-labelledby="tm-cmp-tobe-title"
      >
        <div className="tm-revision-compare-summary__role-row">
          <h4 id="tm-cmp-tobe-title" className="tm-revision-compare-summary__role">
            TO-BE
          </h4>
          <HelpTooltip content={H.toBe} ariaLabel="Ajuda: TO-BE" />
        </div>
        <p className="tm-revision-compare-summary__helper">Cenário proposto</p>
        {mode === "baseline_only" || !toBeLabel ? (
          <p className="tm-revision-compare-summary__value">
            Ainda não há cenário para comparação.
          </p>
        ) : (
          <>
            <p className="tm-revision-compare-summary__value">{toBeLabel}</p>
            {toBeProvenance ? (
              <TmStatusBadge label={provenanceLabelText(toBeProvenance)} variant="neutral" />
            ) : null}
            {calculatedSummary?.toBeEconomy != null ? (
              <p className="tm-revision-compare-summary__metric">
                Economia líquida/mês: {formatProcessoNumber(calculatedSummary.toBeEconomy)}
              </p>
            ) : null}
          </>
        )}
      </article>

      <article
        className="tm-revision-compare-summary__card tm-revision-compare-summary__card--delta"
        aria-labelledby="tm-cmp-delta-title"
      >
        <div className="tm-revision-compare-summary__role-row">
          <h4 id="tm-cmp-delta-title" className="tm-revision-compare-summary__role">
            DELTA
          </h4>
          <HelpTooltip content={H.delta} ariaLabel="Ajuda: DELTA" />
        </div>
        <p className="tm-revision-compare-summary__helper">Diferença calculada</p>
        {mode === "pair" && calculatedSummary?.deltaEconomy != null ? (
          <>
            <p className="tm-revision-compare-summary__value tm-revision-compare-summary__value--emphasis">
              {formatSigned(calculatedSummary.deltaEconomy)}
            </p>
            <TmStatusBadge label="CALCULADO" variant="neutral" />
            <p className="tm-revision-compare-summary__metric">Economia líquida/mês</p>
          </>
        ) : (
          <p className="tm-revision-compare-summary__value">Indisponível</p>
        )}
      </article>
    </div>
  );
}

function formatSigned(value: number): string {
  if (value > 0) return `+${formatProcessoNumber(value)}`;
  return formatProcessoNumber(value);
}
