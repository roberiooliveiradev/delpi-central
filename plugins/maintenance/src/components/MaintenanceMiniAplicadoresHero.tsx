import type { ReactNode } from "react";

import { MaintenancePageHero, MaintenanceStatusBadge } from "../app/maintenanceUi";
import { MiniAplicadoresNav } from "./MiniAplicadoresNav";
import { resolveFilialDisplayName } from "../utils/maintenanceFilialSelection";

type MaintenanceMiniAplicadoresHeroProps = {
  title: ReactNode;
  description?: ReactNode;
  filial: string;
  filialDisplayName?: string;
  moduleHomePath: string;
  showConfiguration?: boolean;
  currentPath?: string;
  onNavigate: (path: string) => void;
  actions?: ReactNode;
};

export function MaintenanceMiniAplicadoresHero({
  title,
  description,
  filial,
  filialDisplayName,
  moduleHomePath,
  showConfiguration = false,
  currentPath,
  onNavigate,
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
    >
      <MiniAplicadoresNav
        currentPath={currentPath}
        moduleHomePath={moduleHomePath}
        showConfiguration={showConfiguration}
        onNavigate={onNavigate}
      />
    </MaintenancePageHero>
  );
}
