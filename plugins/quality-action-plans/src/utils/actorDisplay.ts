export type ActorIdentity = {
  userId?: string | null;
  name?: string | null;
  email?: string | null;
};

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
