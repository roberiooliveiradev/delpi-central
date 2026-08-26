import { formatMaintenanceUpdatedAt } from "../utils/formatMaintenanceUpdatedAt";

type MaintenanceHeroFreshnessProps = {
  updatedAt: Date | null;
};

export function MaintenanceHeroFreshness({ updatedAt }: MaintenanceHeroFreshnessProps) {
  if (!updatedAt) return null;
  return (
    <span className="dm-hero-freshness" aria-live="polite">
      Atualizado às {formatMaintenanceUpdatedAt(updatedAt)}
    </span>
  );
}
