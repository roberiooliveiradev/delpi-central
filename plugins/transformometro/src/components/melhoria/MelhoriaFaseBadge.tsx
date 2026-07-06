import { labelMelhoriaFase, melhoriaFaseBadgeClass } from "../../constants/melhoriaForm";

type Props = {
  fase?: string | null;
};

export function MelhoriaFaseBadge({ fase }: Props) {
  const value = fase?.trim() || "planejado";
  return (
    <span className={`ds-badge ${melhoriaFaseBadgeClass(value)}`}>{labelMelhoriaFase(value)}</span>
  );
}
