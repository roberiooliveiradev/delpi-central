import {
  beneficioCalculoBadgeClass,
  beneficioCalculoLabel,
} from "../content/beneficioCalculoLabels";

type Props = {
  value?: string | null;
  /** Baseline não declara categoria operacional. */
  hideWhenBaseline?: boolean;
  cenarioTipo?: string | null;
};

export function BeneficioCalculoChip({
  value,
  hideWhenBaseline = false,
  cenarioTipo,
}: Props) {
  if (hideWhenBaseline && (cenarioTipo ?? "").toLowerCase() === "baseline") {
    return <span>—</span>;
  }
  const label = beneficioCalculoLabel(value);
  if (label === "—") return <span>—</span>;
  return <span className={beneficioCalculoBadgeClass(value)}>{label}</span>;
}
