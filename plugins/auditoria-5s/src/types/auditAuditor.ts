import { formatPersonName } from "../utils/formatPersonName";

export type AuditAuditorSelection = {
  user_id: string;
  display_name: string;
};

export function createCurrentUserAuditor(
  userId: string | null,
  displayName: string | null,
): AuditAuditorSelection | null {
  if (!userId) return null;
  return {
    user_id: userId,
    display_name: formatPersonName(displayName) || displayName?.trim() || "Usuário",
  };
}
