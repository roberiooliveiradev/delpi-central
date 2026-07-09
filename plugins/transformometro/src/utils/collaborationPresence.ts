import type {
  CollaborationEntityType,
  CollaborationPresencePayload,
} from "../data/api/transformometroCollaborationApi";

export function isMatchingPresencePayload(
  payload: CollaborationPresencePayload,
  entityType: CollaborationEntityType,
  entityId: string
): boolean {
  return payload.entity_type === entityType && payload.entity_id === entityId;
}
