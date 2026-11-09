/** Participant/signer draft helpers for the meeting-minute editor.

Backend persists participants and signers as distinct tables. Signers are
derived from must_sign + identity (user_id or invite_email). Name-only
internal rows (no user_id) cannot sign and must not inflate the Assina UI.
*/

export type ParticipantDraft = {
  /** Stable client identity — never rely on nullable user_id alone. */
  client_key: string;
  user_id?: string;
  display_name: string;
  role_in_meeting: string;
  must_sign: boolean;
  is_external: boolean;
  invite_email?: string;
  /** True when loaded without Delpi user_id (legacy / TÉO name-only). */
  unresolved_identity?: boolean;
};

type ApiParticipant = {
  user_id?: string | null;
  display_name?: string | null;
  role_in_meeting?: string | null;
  must_sign?: boolean | null;
  is_external?: boolean | null;
};

type ApiSigner = {
  user_id?: string | null;
  display_name?: string | null;
  invite_email?: string | null;
};

let _keySeq = 0;

export function nextParticipantClientKey(prefix = "p"): string {
  _keySeq += 1;
  return `${prefix}-${_keySeq}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Eligible signer for save/send — identity required. */
export function isSigner(item: ParticipantDraft): boolean {
  if (!item.must_sign || !item.display_name.trim()) return false;
  if (item.unresolved_identity) return false;
  if (item.is_external) {
    return Boolean(item.invite_email?.trim() && item.invite_email.includes("@"));
  }
  return Boolean(item.user_id);
}

export function hydrateParticipantsFromDetail(
  participants: ApiParticipant[],
  signers: ApiSigner[],
): ParticipantDraft[] {
  return participants.map((item) => {
    const name = String(item.display_name ?? "");
    const userId = item.user_id ? String(item.user_id) : undefined;
    const isExternal = Boolean(item.is_external);
    const unresolved = !isExternal && !userId;
    const matchingSigner = signers.find((signer) => {
      if (userId && String(signer.user_id ?? "") === userId) return true;
      if (!userId && String(signer.display_name ?? "") === name) return true;
      return false;
    });
    // Authoritative must_sign only counts when identity exists; unresolved
    // name-only rows stay presence-only in the editor until linked.
    const mustSign = unresolved ? false : Boolean(item.must_sign);
    return {
      client_key: nextParticipantClientKey(userId ? "u" : "orphan"),
      user_id: userId,
      display_name: name,
      role_in_meeting: String(item.role_in_meeting ?? "participant"),
      must_sign: mustSign,
      is_external: isExternal,
      invite_email: matchingSigner?.invite_email
        ? String(matchingSigner.invite_email)
        : undefined,
      unresolved_identity: unresolved || undefined,
    };
  });
}

export function draftFromDirectoryUser(
  user: { id: string; name?: string; email?: string },
  previous?: ParticipantDraft,
): ParticipantDraft {
  // Linking an unresolved name-only row defaults to must_sign=true so the
  // Assina counter becomes coherent immediately after directory pick.
  const mustSign = previous?.unresolved_identity
    ? true
    : (previous?.must_sign ?? true);
  return {
    client_key: previous?.client_key ?? nextParticipantClientKey("u"),
    user_id: user.id,
    display_name: user.name || user.email || user.id,
    role_in_meeting: previous?.role_in_meeting ?? "participant",
    must_sign: mustSign,
    is_external: false,
  };
}
