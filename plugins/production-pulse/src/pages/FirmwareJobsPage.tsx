import { useEffect } from "react";

import { PpHintAction, PpPageHero, PpStateBox, ppShellIcon } from "../app/productionPulseUi";
import { productionPulseFirmwareLinksPath } from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareJobsPageProps = {
  branch: string;
};

/** Legacy `/firmware-jobs` — redirects to Admin hub jobs panel. */
export function FirmwareJobsPage({ branch }: FirmwareJobsPageProps) {
  useEffect(() => {
    navigateProductionPulse(
      productionPulseFirmwareLinksPath({ branch, panel: "jobs", focus: "jobs" }),
    );
  }, [branch]);

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Admin"
        badge={ppShellIcon}
        description={PP_HELP.ota.jobsHero}
        actions={
          <PpHintAction hint={PP_HELP.ota.openLinks} ariaLabel="Ajuda: Admin mapa">
            <span className="pp-muted">Redirecionando…</span>
          </PpHintAction>
        }
      />
      <PpStateBox variant="loading" title="Redirecionando para o mapa Admin…" />
    </div>
  );
}
