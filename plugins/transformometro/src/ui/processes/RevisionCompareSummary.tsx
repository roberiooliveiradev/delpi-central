import { TmStatusBadge } from "../../components/tmChromeUi";
import { formatProcessoNumber } from "../../utils/processoDetailTables";
import {
  provenanceLabelText,
  type ProvenanceLabel,
} from "./buildRevisionComparisonView";

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
      <article className="tm-revision-compare-summary__card" aria-labelledby="tm-cmp-asis-title">
        <h4 id="tm-cmp-asis-title" className="tm-revision-compare-summary__role">
          AS-IS
        </h4>
        <p className="tm-revision-compare-summary__value">{asIsLabel}</p>
        <TmStatusBadge label={provenanceLabelText(asIsProvenance)} variant="neutral" />
        {calculatedSummary?.asIsEconomy != null ? (
          <p className="ds-hint">
            Economia líquida/mês (calc.): {formatProcessoNumber(calculatedSummary.asIsEconomy)}
          </p>
        ) : null}
      </article>

      <article className="tm-revision-compare-summary__card" aria-labelledby="tm-cmp-tobe-title">
        <h4 id="tm-cmp-tobe-title" className="tm-revision-compare-summary__role">
          TO-BE
        </h4>
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
              <p className="ds-hint">
                Economia líquida/mês (calc.): {formatProcessoNumber(calculatedSummary.toBeEconomy)}
              </p>
            ) : null}
          </>
        )}
      </article>

      <article className="tm-revision-compare-summary__card" aria-labelledby="tm-cmp-delta-title">
        <h4 id="tm-cmp-delta-title" className="tm-revision-compare-summary__role">
          DELTA
        </h4>
        {mode === "pair" && calculatedSummary?.deltaEconomy != null ? (
          <>
            <p className="tm-revision-compare-summary__value">
              {formatSigned(calculatedSummary.deltaEconomy)}
            </p>
            <TmStatusBadge label="CALCULADO" variant="neutral" />
            <p className="ds-hint">Diferença de economia líquida/mês (contrato de comparação).</p>
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
