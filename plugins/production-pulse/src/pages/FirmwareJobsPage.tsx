import { useEffect } from "react";

import { PpHintAction, PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";
import { productionPulseFirmwareLinksPath } from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareJobsPageProps = {
  branch: string;
};

/** Legacy `/firmware-jobs` — redirects to the OTA hub (`/firmware-links`). */
export function FirmwareJobsPage({ branch }: FirmwareJobsPageProps) {
  useEffect(() => {
    navigateProductionPulse(productionPulseFirmwareLinksPath({ branch }));
  }, [branch]);

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Hub OTA"
        badge={ppShellIcon}
        description={PP_HELP.ota.jobsHero}
        actions={
          <PpHintAction hint={PP_HELP.ota.openLinks} ariaLabel="Ajuda: Hub OTA">
            <span className="pp-muted">Redirecionando…</span>
          </PpHintAction>
        }
      />
      <PpStateBox variant="loading" title="Redirecionando para o hub OTA…" />
    </div>
  );
}
