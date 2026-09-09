import { useEffect } from "react";

import { PpHintAction, PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";
import { productionPulseFirmwareLinksPath } from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

/** Legacy `/firmwares` — o catálogo agora vive na seção Firmwares do hub OTA. */
export function FirmwaresPage() {
  useEffect(() => {
    navigateProductionPulse(productionPulseFirmwareLinksPath({ focus: "catalog" }));
  }, []);

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Hub OTA"
        badge={ppShellIcon}
        description={PP_HELP.hub.catalog}
        actions={
          <PpHintAction hint={PP_HELP.ota.openLinks} ariaLabel="Ajuda: Hub OTA">
            <span className="pp-muted">Redirecionando…</span>
          </PpHintAction>
        }
      />
      <PpStateBox variant="loading" title="Redirecionando…" />
    </div>
  );
}
