import { SCORE_OPTIONS } from "../constants/audit5s";

type ScoreTone = "low" | "mid" | "high" | "na";

type Props = {
  disabled: boolean;
  score: number | null | undefined;
  isNotApplicable: boolean;
  onSelect: (payload: { score: number | null; is_not_applicable: boolean }) => void;
};

const SCORE_META: Record<number, { tone: ScoreTone; label: string }> = {
  1: { tone: "low", label: "Ruim" },
  3: { tone: "mid", label: "Médio" },
  5: { tone: "high", label: "Bom" },
};

export { getScoreSummaryLabel } from "../utils/scoreLabels";

export function getScoreTone(
  score: number | null | undefined,
  isNotApplicable: boolean,
): ScoreTone | null {
  if (isNotApplicable) return "na";
  if (score === 1) return "low";
  if (score === 3) return "mid";
  if (score === 5) return "high";
  return null;
}

export function CriterionScorePicker({ disabled, score, isNotApplicable, onSelect }: Props) {
  return (
    <div className="a5s-score-picker" role="radiogroup" aria-label="Nota do critério">
      {SCORE_OPTIONS.map((option) => {
        const meta = SCORE_META[option.value];
        const selected = !isNotApplicable && score === option.value;

        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            className={`a5s-score-option a5s-score-option--${meta.tone} ${
              selected ? "a5s-score-option--selected" : ""
            }`}
            onClick={() => onSelect({ score: option.value, is_not_applicable: false })}
          >
            {meta.label}
          </button>
        );
      })}

      <button
        type="button"
        role="radio"
        aria-checked={isNotApplicable}
        disabled={disabled}
        className={`a5s-score-option a5s-score-option--na ${
          isNotApplicable ? "a5s-score-option--selected" : ""
        }`}
        onClick={() => onSelect({ score: null, is_not_applicable: true })}
      >
        N/A
      </button>
    </div>
  );
}
