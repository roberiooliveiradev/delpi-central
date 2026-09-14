/**
 * Socket.IO auth helpers for Portal ↔ core-api.
 * Auth is validated only on Engine.IO handshake; keep socket.auth fresh
 * before every connect/reconnect (silent Keycloak refresh updates tokenRef only).
 */

export const SOCKET_TOKEN_MIN_LENGTH = 20;

export function resolveSocketAccessToken(
  token: string | undefined | null,
): string | null {
  const value = typeof token === "string" ? token.trim() : "";
  return value.length >= SOCKET_TOKEN_MIN_LENGTH ? value : null;
}

/** Start a new connect only when the manager is idle (not connected/reconnecting). */
export function shouldStartSocketConnect(params: {
  connected: boolean;
  active: boolean;
}): boolean {
  return !params.connected && !params.active;
}

export type ApplySocketAuthResult = "skipped" | "auth_updated" | "connecting";

export function applySocketAuthToken(
  socket: {
    auth: Record<string, unknown> | ((cb: (data: object) => void) => void);
    connected: boolean;
    active: boolean;
    connect: () => void;
  },
  token: string | undefined | null,
): ApplySocketAuthResult {
  const resolved = resolveSocketAccessToken(token);
  if (!resolved) {
    return "skipped";
  }

  socket.auth = { token: resolved };

  if (
    shouldStartSocketConnect({
      connected: socket.connected,
      active: socket.active,
    })
  ) {
    socket.connect();
    return "connecting";
  }

  return "auth_updated";
}
