import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { navigateTransformometro } from "./navigation";

export function buildTransformometroUserPath(userId: string): string | null {
  const id = (userId || "").trim();
  if (!id) return null;
  return `${TRANSFORMOMETRO_ROUTES.home}/users/${encodeURIComponent(id)}`;
}

/**
 * Perfil do Portal Transforma+ (`/users/:id`) — próprio e de outros.
 * Identidade global Minha DELPI (`/profile`) é do shell do host.
 */
export function navigateTransformometroUserProfile(
  userId: string,
  _currentUserId?: string | null,
): boolean {
  const path = buildTransformometroUserPath(userId);
  if (!path) return false;
  navigateTransformometro(path);
  return true;
}

export function transformometroUserLinkTitle(name: string): string {
  const label = (name || "").trim() || "usuário";
  return `Abrir perfil de ${label}`;
}
