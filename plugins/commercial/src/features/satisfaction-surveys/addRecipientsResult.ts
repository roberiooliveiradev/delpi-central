import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import type { SatisfactionAddRecipientsResult } from "../../types/satisfactionSurvey";

export type AddRecipientsFeedback = {
  success: string | null;
  info: string | null;
  failures: string[];
};

/**
 * Traduz o resultado parcial do lote em avisos (sem painel de contadores — decisão UI-02B.1).
 * Inclusões válidas valem mesmo com outras falhando; duplicadas preservam vínculo/token.
 */
export function describeAddRecipientsResult(
  result: SatisfactionAddRecipientsResult,
): AddRecipientsFeedback {
  const copy = SATISFACTION_CONTENT.participants;
  const included = result.counts?.included ?? result.included?.length ?? 0;
  const existing = result.counts?.already_existing ?? result.already_existing?.length ?? 0;
  return {
    success: included > 0 ? copy.addIncluded(included) : null,
    info: existing > 0 ? copy.addExisting(existing) : null,
    failures: (result.failed ?? []).map((failure) =>
      copy.addFailed(`${failure.customer_code}/${failure.customer_store}`, failure.message),
    ),
  };
}
