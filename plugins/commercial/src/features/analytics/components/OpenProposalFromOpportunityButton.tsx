import { useState, type MouseEvent } from "react";

import { CommercialActionButton } from "../../app/commercialUi";
import { currentLocationAsReturnTo } from "../../app/commercialNavigationReturn";
import { useCommercialFloatingNotice } from "../../app/CommercialFloatingNoticeProvider";
import { navigateProposalDetail } from "../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { resolveProposalDocumentForOpportunity } from "../../utils/resolveProposalDocumentForOpportunity";

type OpenProposalFromOpportunityButtonProps = {
  basePath: string;
  opportunityNumber: string;
  returnLabel?: string;
};

export function OpenProposalFromOpportunityButton({
  basePath,
  opportunityNumber,
  returnLabel,
}: OpenProposalFromOpportunityButtonProps) {
  const { notifyError, notifySuccess } = useCommercialFloatingNotice();
  const [busy, setBusy] = useState(false);
  const copy = ANALYTICS_CONTENT.oportunidades;

  const onClick = async (event: MouseEvent) => {
    event.stopPropagation();
    if (busy) return;
    setBusy(true);
    try {
      const result = await resolveProposalDocumentForOpportunity(opportunityNumber);
      if (result.status === "none") {
        notifyError(copy.openProposalEmpty);
        return;
      }
      const opened = navigateProposalDetail(result.item.proposta_interna, {
        basePath,
        returnNav: {
          returnTo: currentLocationAsReturnTo(),
          returnLabel: returnLabel || copy.openProposalReturnLabel,
        },
      });
      if (!opened) {
        notifyError(copy.openProposalEmpty);
        return;
      }
      if (result.matchCount > 1) {
        notifySuccess(copy.openProposalMultipleHint);
      }
    } catch (err: unknown) {
      notifyError(err instanceof Error ? err.message : copy.openProposalError);
    } finally {
      setBusy(false);
    }
  };

  return (
    <CommercialActionButton variant="ghost" disabled={busy} onClick={onClick}>
      {busy ? copy.openProposalBusy : copy.openProposal}
    </CommercialActionButton>
  );
}
