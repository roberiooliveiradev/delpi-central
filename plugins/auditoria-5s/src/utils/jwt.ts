import { formatPersonName } from "./formatPersonName";

type JwtPayload = {
  sub?: string;
  name?: string;
  preferred_username?: string;
  given_name?: string;
  family_name?: string;
  email?: string;
};

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(
    normalized.length + ((4 - (normalized.length % 4)) % 4),
    "=",
  );
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}

function parseJwtPayload(token: string): JwtPayload | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;

  try {
    return JSON.parse(decodeBase64Url(parts[1])) as JwtPayload;
  } catch {
    return null;
  }
}

export function getUserIdFromToken(token: string | undefined): string | null {
  if (!token) return null;
  return parseJwtPayload(token)?.sub ?? null;
}

export function getFullDisplayNameFromToken(token: string | undefined): string | null {
  if (!token) return null;

  const payload = parseJwtPayload(token);
  if (!payload) return null;

  const fullName = payload.name?.trim();
  if (fullName) return formatPersonName(fullName);

  const composed = [payload.given_name?.trim(), payload.family_name?.trim()]
    .filter(Boolean)
    .join(" ");
  if (composed) return formatPersonName(composed);

  const username = payload.preferred_username?.trim();
  if (username) return formatPersonName(username.split("@")[0] ?? username);

  const email = payload.email?.trim();
  if (email) return formatPersonName(email.split("@")[0] ?? email);

  return null;
}

export function getDisplayNameFromToken(token: string | undefined): string | null {
  const fullName = getFullDisplayNameFromToken(token);
  if (!fullName) return null;
  return fullName.split(/\s+/)[0] ?? fullName;
}
