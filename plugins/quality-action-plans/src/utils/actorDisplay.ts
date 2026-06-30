import { formatPersonName } from "./formatPersonName";

export type ActorIdentity = {
  userId?: string | null;
  name?: string | null;
  email?: string | null;
};

/** Nome legível de quem submeteu eficácia (coluna «Por»). */
export function formatEffectivenessSubmittedBy(input: {
  effectiveness_submitted_by_name?: string | null;
  effectiveness_submitted_by?: string | null;
}): string {
  const name = formatPersonName(input.effectiveness_submitted_by_name);
  if (name) return name;
  const userId = input.effectiveness_submitted_by?.trim();
  return userId || "—";
}

/** Rótulo legível para «Por …» na linha do tempo e auditoria. */
export function formatActorDisplay(actor: ActorIdentity): string | undefined {
  const name = actor.name?.trim();
  const email = actor.email?.trim();
  const userId = actor.userId?.trim();

  if (name && email) {
    return `Por ${name} (${email})`;
  }
  if (name) {
    return `Por ${name}`;
  }
  if (email) {
    return `Por ${email}`;
  }
  if (userId) {
    return `Por ${userId}`;
  }
  return undefined;
}
