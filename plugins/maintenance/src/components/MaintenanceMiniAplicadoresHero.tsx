import type { ReactNode } from "react";

import { MaintenancePageHero, MaintenanceStatusBadge } from "../app/maintenanceUi";
import { resolveFilialDisplayName } from "../utils/maintenanceFilialSelection";

type MaintenanceMiniAplicadoresHeroProps = {
  title: ReactNode;
  description?: ReactNode;
  filial: string;
  filialDisplayName?: string;
  actions?: ReactNode;
};

export function MaintenanceMiniAplicadoresHero({
  title,
  description,
  filial,
  filialDisplayName,
  actions,
}: MaintenanceMiniAplicadoresHeroProps) {
  const badgeLabel = filialDisplayName ?? resolveFilialDisplayName([], filial) ?? filial;

  return (
    <MaintenancePageHero
      eyebrow="DELPI • Manutenção • Mini-aplicadores"
      title={title}
      description={description}
      badge={
        <MaintenanceStatusBadge variant="info" label={badgeLabel} />
      }
      actions={actions}
    />
  );
}
