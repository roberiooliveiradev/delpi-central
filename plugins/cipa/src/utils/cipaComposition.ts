import type { CipaMember } from "../api/cipaApi";

export type CompositionParticipantDraft = {
  user_id?: string;
  display_name: string;
  role_in_meeting: string;
  presence: string;
  is_external: boolean;
  must_sign: boolean;
};

/** Converte a composição vigente da CIPA em participantes de nova ata (snapshot). */
export function membersToParticipantDrafts(
  members: CipaMember[],
): CompositionParticipantDraft[] {
  return members.map((member) => ({
    user_id: String(member.user_id),
    display_name: String(member.display_name || "").trim() || "Membro CIPA",
    role_in_meeting: String(member.role || "titular_member"),
    presence: "present",
    is_external: false,
    must_sign: true,
  }));
}

/**
 * Mescla composição recarregada com externos já adicionados manualmente.
 * Internos anteriores são substituídos pela composição vigente.
 */
export function mergeCompositionWithExternals(
  members: CipaMember[],
  current: CompositionParticipantDraft[],
): CompositionParticipantDraft[] {
  const externals = current.filter((item) => item.is_external);
  return [...membersToParticipantDrafts(members), ...externals];
}
