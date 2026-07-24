export type CollaborativeEntityUpdateInput = {
  editingSectionKey: string | null;
  updatedSectionKey?: string | null;
  actorUserId?: string | null;
  myUserId?: string | null;
  /** Aba/cliente que originou a mutação (preferido para ignore_own). */
  actorClientId?: string | null;
  myClientId?: string | null;
  updatedSectionLabel?: string | null;
};

export type CollaborativeEntityUpdateResult =
  | { kind: "ignore_own" }
  | { kind: "block_editing_conflict"; notice: string }
  | { kind: "resync"; notice: string | null };

const CONFLICT_NOTICE =
  "Outro usuário alterou esta seção. Salve ou cancele a edição e recarregue para ver as mudanças.";

export function resolveCollaborativeEntityUpdate(
  input: CollaborativeEntityUpdateInput
): CollaborativeEntityUpdateResult {
  const {
    editingSectionKey,
    updatedSectionKey,
    actorClientId,
    myClientId,
    updatedSectionLabel,
  } = input;

  // Anti-eco só na mesma aba/cliente — outras abas do mesmo user sincronizam via WS.
  if (actorClientId && myClientId && actorClientId === myClientId) {
    return { kind: "ignore_own" };
  }

  const sectionLabel = updatedSectionLabel?.trim() || null;

  if (editingSectionKey) {
    const affectsEditingSection =
      !updatedSectionKey || updatedSectionKey === editingSectionKey;

    if (affectsEditingSection) {
      return { kind: "block_editing_conflict", notice: CONFLICT_NOTICE };
    }

    const notice = sectionLabel
      ? `Outro usuário atualizou ${sectionLabel}. Os demais dados foram recarregados.`
      : "Outro usuário atualizou outra seção. Os demais dados foram recarregados.";

    return { kind: "resync", notice };
  }

  const notice = sectionLabel
    ? `${sectionLabel} atualizado por outro usuário.`
    : "Dados atualizados por outro usuário.";

  return { kind: "resync", notice };
}
