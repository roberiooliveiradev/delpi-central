import type { ReactNode } from "react";

import { PpTopBar } from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import type { ProductionPulseRoute } from "../constants/routes";
import {
  productionPulseFirmwareLinksPath,
  productionPulseOperatorPath,
  PRODUCTION_PULSE_BASE_PATH,
} from "../constants/routes";
import { SHELL_NAV_CONTENT, resolveShellNavItems } from "../content/shellNav";
import { navigateProductionPulse } from "../utils/navigation";
import { resolvePulseNavId, type ProductionPulseNavId } from "../utils/resolvePulseNavId";

type ProductionPulseShellProps = {
  route: ProductionPulseRoute;
  permissions: ProductionPulsePermissionFlags;
  children: ReactNode;
};

function navPath(id: ProductionPulseNavId, route: ProductionPulseRoute): string {
  switch (id) {
    case "panel":
      return PRODUCTION_PULSE_BASE_PATH;
    case "hub":
      return productionPulseFirmwareLinksPath({
        branch: route.kind === "firmwareLinks" ? route.branch : "01",
      });
    case "operator":
      return productionPulseOperatorPath({ branch: "01" });
    default:
      return PRODUCTION_PULSE_BASE_PATH;
  }
}

export function ProductionPulseShell({ route, permissions, children }: ProductionPulseShellProps) {
  const activeId = resolvePulseNavId(route);
  const items = resolveShellNavItems({ canOperator: permissions.canOperator });

  return (
    <div className="pp-shell">
      <PpTopBar
        aria-label={SHELL_NAV_CONTENT.ariaLabel}
        activeId={activeId ?? ""}
        collapsible
        menuLabel={SHELL_NAV_CONTENT.menuLabel}
        portalScopeClassName="dashboard-production-pulse"
        items={items.map((item) => ({
          id: item.id,
          label: item.label,
          onSelect: () => navigateProductionPulse(navPath(item.id, route)),
        }))}
      />
      <div className="pp-shell__content">{children}</div>
    </div>
  );
}
