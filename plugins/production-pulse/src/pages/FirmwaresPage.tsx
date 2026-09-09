import { useEffect } from "react";

import { PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";
import { productionPulseFirmwareLinksPath } from "../constants/routes";
import { navigateProductionPulse } from "../utils/navigation";

/** Legacy list path → Admin hub firmwares panel. */
export function FirmwaresPage() {
  useEffect(() => {
    navigateProductionPulse(productionPulseFirmwareLinksPath({ focus: "catalog", panel: "firmwares" }));
  }, []);

  return (
    <div className="pp-page-stack">
      <PpPageHero title="Admin" badge={ppShellIcon} />
      <PpStateBox variant="loading" title="Redirecionando para o catálogo no mapa…" />
    </div>
  );
}
