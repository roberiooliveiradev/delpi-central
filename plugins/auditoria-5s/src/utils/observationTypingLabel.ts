import type { AuditTypingUser } from "../constants/realtime";
import { formatPersonName } from "./formatPersonName";

export function formatObservationTypingLabel(
  users: AuditTypingUser[],
  selfClientId: string,
): string | null {
  const others = users.filter((user) => user.client_id !== selfClientId);
  if (others.length === 0) return null;

  const names = [
    ...new Set(
      others
        .map((user) => formatPersonName(user.display_name))
        .filter(Boolean),
    ),
  ];

  if (names.length === 1) {
    return `${names[0]} está comentando…`;
  }

  if (names.length === 2) {
    return `${names[0]} e ${names[1]} estão comentando…`;
  }

  return `${names.length} pessoas estão comentando…`;
}
