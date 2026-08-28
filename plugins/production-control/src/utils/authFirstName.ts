import { peekAccessToken } from "../api/httpClient";

type JwtPayload = {
  name?: string;
  given_name?: string;
  preferred_username?: string;
  email?: string;
};

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
  return atob(padded);
}

function cleanName(value: string | undefined): string | null {
  const normalized = value?.trim();
  if (!normalized) return null;
  if (normalized.includes("@")) {
    return normalized.split("@")[0] || null;
  }
  return normalized;
}

/** Primeiro nome a partir do JWT do portal (given_name → name → username → e-mail). */
export function resolveUserFirstName(): string | null {
  const token = peekAccessToken();
  if (!token) return null;
  const payloadPart = token.split(".")[1];
  if (!payloadPart) return null;
  try {
    const payload = JSON.parse(decodeBase64Url(payloadPart)) as JwtPayload;
    const full =
      cleanName(payload.given_name) ||
      cleanName(payload.name) ||
      cleanName(payload.preferred_username) ||
      cleanName(payload.email);
    if (!full) return null;
    return full.split(/\s+/)[0] || null;
  } catch {
    return null;
  }
}
