import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import { localInputToIso } from "./satisfactionDates";

export type CampaignFormValues = {
  name: string;
  startsAtIso: string;
  endsAtIso: string;
};

/** Validação pura (testável): nome obrigatório, datas válidas e início < término. */
export function validateCampaignForm(input: {
  name: string;
  startsAtLocal: string;
  endsAtLocal: string;
}): { ok: true; values: CampaignFormValues } | { ok: false; message: string } {
  const copy = SATISFACTION_CONTENT.campaignForm;
  const name = input.name.trim();
  if (!name) return { ok: false, message: copy.nameRequired };
  const startsAtIso = localInputToIso(input.startsAtLocal);
  const endsAtIso = localInputToIso(input.endsAtLocal);
  if (!startsAtIso || !endsAtIso) return { ok: false, message: copy.datesRequired };
  if (new Date(startsAtIso).getTime() >= new Date(endsAtIso).getTime()) {
    return { ok: false, message: copy.datesOrder };
  }
  return { ok: true, values: { name, startsAtIso, endsAtIso } };
}
