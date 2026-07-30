import type { ComiteEticaMember } from "../api/cecApi";

export type CompositionParticipantDraft = {
  user_id?: string;
  display_name: string;
  role_in_meeting: string;
  presence: string;
  is_external: boolean;
  must_sign: boolean;
};

/** Converte a composição vigente do Comitê de Ética em participantes de nova ata (snapshot). */
export function membersToParticipantDrafts(
  members: ComiteEticaMember[],
): CompositionParticipantDraft[] {
  return members.map((member) => {
    const role = String(member.role || "member");
    return {
      user_id: String(member.user_id),
      display_name: String(member.display_name || "").trim() || "Membro do Comitê",
      role_in_meeting: role,
      presence: "present",
      is_external: false,
      must_sign: role !== "guest",
    };
  });
}

/**
 * Mescla composição recarregada com externos já adicionados manualmente.
 * Internos anteriores são substituídos pela composição vigente.
 */
export function mergeCompositionWithExternals(
  members: ComiteEticaMember[],
  current: CompositionParticipantDraft[],
): CompositionParticipantDraft[] {
  const externals = current.filter((item) => item.is_external);
  return [...membersToParticipantDrafts(members), ...externals];
}
