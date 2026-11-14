import { CommercialStatusBadge } from "../../app/commercialUi";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionCampaignStatus } from "../../types/satisfactionSurvey";

const VARIANT: Record<SatisfactionCampaignStatus, "info" | "success" | "neutral"> = {
  scheduled: "info",
  open: "success",
  closed: "neutral",
};

export function campaignStatusLabel(status: SatisfactionCampaignStatus): string {
  return SATISFACTION_CONTENT.status[status] ?? status;
}

/** A situação vem calculada pela API; o frontend só apresenta. */
export function SatisfactionStatusBadge({ status }: { status: SatisfactionCampaignStatus }) {
  return (
    <CommercialStatusBadge
      label={campaignStatusLabel(status)}
      variant={VARIANT[status] ?? "neutral"}
    />
  );
}
