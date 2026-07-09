import type {
  CollaborationEntityType,
  CollaborationPresencePayload,
  CollaborationPresenceUser,
} from "../data/api/transformometroCollaborationApi";

export function isMatchingPresencePayload(
  payload: CollaborationPresencePayload,
  entityType: CollaborationEntityType,
  entityId: string
): boolean {
  return payload.entity_type === entityType && payload.entity_id === entityId;
}

function normalizePresenceUsers(users: CollaborationPresenceUser[]) {
  return [...users]
    .map((user) => ({
      user_id: user.user_id ?? "",
      user_name: user.user_name ?? "",
      user_email: user.user_email ?? "",
      section_key: user.section_key,
      mode: user.mode,
      lock_active: Boolean(user.lock_active),
    }))
    .sort((left, right) =>
      `${left.user_id}:${left.section_key}`.localeCompare(`${right.user_id}:${right.section_key}`)
    );
}

/** Evita re-render quando o snapshot de presença não mudou semanticamente. */
export function presencePayloadEquals(
  current: CollaborationPresencePayload | null,
  next: CollaborationPresencePayload | null
): boolean {
  if (current === next) {
    return true;
  }
  if (!current || !next) {
    return false;
  }
  if (current.entity_type !== next.entity_type || current.entity_id !== next.entity_id) {
    return false;
  }
  return (
    JSON.stringify(normalizePresenceUsers(current.viewers)) ===
      JSON.stringify(normalizePresenceUsers(next.viewers)) &&
    JSON.stringify(normalizePresenceUsers(current.editors)) ===
      JSON.stringify(normalizePresenceUsers(next.editors))
  );
}
