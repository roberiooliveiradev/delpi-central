import { useRef, useState } from "react";

import {
  AnchoredPanelPortal,
  PpActionButton,
  PpHintAction,
} from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { HubOtaKpis } from "../utils/hubOtaKpis";

type HubOtaKpiChipsProps = {
  kpis: HubOtaKpis;
  loading?: boolean;
  activeJobs?: number;
  onOpenJobs?: () => void;
};

export function HubOtaKpiChips({
  kpis,
  loading,
  activeJobs = 0,
  onOpenJobs,
}: HubOtaKpiChipsProps) {
  const anchorRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);

  if (loading) {
    return (
      <div className="pp-hub-kpi-chips" aria-label="Indicadores OTA">
        <span className="pp-hub-chip pp-hub-chip--skeleton" />
        <span className="pp-hub-chip pp-hub-chip--skeleton" />
        <span className="pp-hub-chip pp-hub-chip--skeleton" />
      </div>
    );
  }

  return (
    <div className="pp-hub-kpi-chips" aria-label="Indicadores OTA">
      <PpHintAction hint={PP_HELP.hub.kpiPublished} ariaLabel="Ajuda: saúde da frota">
        <button
          ref={anchorRef}
          type="button"
          className="pp-hub-chip"
          aria-expanded={open}
          aria-haspopup="dialog"
          onClick={() => setOpen((value) => !value)}
        >
          Saúde da frota ▾
        </button>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.kpiLinked} ariaLabel="Ajuda: IoTs vinculados">
        <span className="pp-hub-chip pp-hub-chip--static">
          {kpis.linkedDevices} IoTs vinculados
        </span>
      </PpHintAction>
      <PpHintAction hint={PP_HELP.hub.kpiOutdated} ariaLabel="Ajuda: desatualizados">
        <span className="pp-hub-chip pp-hub-chip--static">
          {kpis.outdatedDevices} desatualizados
        </span>
      </PpHintAction>
      {onOpenJobs ? (
        <PpHintAction hint={PP_HELP.hub.kpiJobsChip} ariaLabel="Ajuda: Jobs OTA">
          <PpActionButton variant="ghost" className="pp-hub-chip-btn" onClick={onOpenJobs}>
            Jobs OTA ({activeJobs})
          </PpActionButton>
        </PpHintAction>
      ) : null}
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        preferredPlacement="bottom"
        portalScopeClassName="dashboard-production-pulse"
        onDismiss={() => setOpen(false)}
      >
        <div ref={panelRef} className="pp-hub-health-popover" role="dialog" aria-label="Saúde da frota">
          <div>{kpis.publishedFirmwares} firmwares publicados</div>
          <div>{kpis.linkedDevices} IoTs vinculados</div>
          <div>
            {kpis.outdatedDevices} {PP_HELP.hub.kpiOutdatedSuffix}
          </div>
          <div>{kpis.updatingDevices} em atualização</div>
          <div>{kpis.failedDevices} falhas OTA</div>
        </div>
      </AnchoredPanelPortal>
    </div>
  );
}
