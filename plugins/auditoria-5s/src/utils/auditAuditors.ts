import { getAccessToken } from "../api/httpClient";
import { createCurrentUserAuditor, type AuditAuditorSelection } from "../types/auditAuditor";
import { getFullDisplayNameFromToken, getUserIdFromToken } from "./jwt";

export function buildDefaultAuditors(): AuditAuditorSelection[] {
  const token = getAccessToken();
  const current = createCurrentUserAuditor(
    getUserIdFromToken(token),
    getFullDisplayNameFromToken(token),
  );
  return current ? [current] : [];
}
