import {
  ConversationReception,
  UnifiedAvatar,
  firstNameFromDisplay,
  formatPortalGreeting,
} from "@delpi/plugin-ui/index";
import type { DeliaCurrentUserIdentity } from "../identity/currentUser";

/**
 * S2-A + S3 + greeting — reception surface for a session with no turns.
 *
 * Chat-first identity: the DÉLIA glyph (Sparkles, same mark the
 * Portal dock uses for DÉLIA) — never the DELPI/Minha DELPI logo.
 * Honest by contract: no capability cards, no promised features —
 * the copy states only that answers depend on the sources and
 * permissions actually available.
 *
 * Greeting reuses the canonical Portal projections
 * (`firstNameFromDisplay` + `formatPortalGreeting`/`portalDayPeriodGreeting`)
 * over the already-resolved presentation identity — LOCAL_BROWSER_TIME
 * is PRESENTATION_ONLY. No name → no greeting element; nothing is
 * invented. displayName never implies authorization.
 */
export function DeliaReception({
  userIdentity,
}: {
  userIdentity?: DeliaCurrentUserIdentity | null;
}) {
  const firstName = firstNameFromDisplay(userIdentity?.displayName);
  const greeting = firstName
    ? `${formatPortalGreeting({ firstName })}.`
    : undefined;

  return (
    <ConversationReception
      avatar={
        <UnifiedAvatar
          kind="assistant"
          label="DÉLIA"
          size="lg"
          motionState="idle"
        />
      }
      greeting={greeting}
      title="Como posso ajudar você hoje?"
      description="Converse com a inteligência operacional da DELPI. As respostas dependem das informações e permissões disponíveis no momento."
      note="A conversa é mantida apenas nesta tela e não é salva."
    />
  );
}
