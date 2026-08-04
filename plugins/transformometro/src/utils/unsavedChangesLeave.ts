export type UnsavedLeaveGuard = {
  isEditing: () => boolean;
  isDirty: () => boolean;
  save: () => Promise<void>;
  discard: () => void;
};

/**
 * Decide se a navegação pode seguir diante de editores abertos.
 * `choose` só é chamado quando há dirty (salvar / sair / ficar).
 */
export async function resolveUnsavedLeave(
  guards: UnsavedLeaveGuard[],
  choose: () => Promise<"confirm" | "secondary" | "cancel">,
): Promise<boolean> {
  const active = guards.filter((guard) => guard.isEditing());
  if (active.length === 0) return true;

  const dirty = active.filter((guard) => guard.isDirty());
  if (dirty.length === 0) {
    for (const guard of active) guard.discard();
    return true;
  }

  const choice = await choose();
  if (choice === "cancel") return false;

  if (choice === "confirm") {
    for (const guard of active) guard.discard();
    return true;
  }

  try {
    for (const guard of dirty) {
      await guard.save();
    }
    for (const guard of active) {
      if (guard.isEditing()) guard.discard();
    }
    return true;
  } catch {
    return false;
  }
}
