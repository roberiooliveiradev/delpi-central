export function getUserIdFromToken(token: string | undefined): string | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))) as {
      sub?: string;
    };
    return payload.sub ?? null;
  } catch {
    return null;
  }
}

import { formatPersonName } from "./formatPersonName";

export function getFullDisplayNameFromToken(token: string | undefined): string | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))) as {
      name?: string;
      preferred_username?: string;
      given_name?: string;
      family_name?: string;
      email?: string;
    };

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
  } catch {
    return null;
  }
}

export function getDisplayNameFromToken(token: string | undefined): string | null {
  const fullName = getFullDisplayNameFromToken(token);
  if (!fullName) return null;
  return fullName.split(/\s+/)[0] ?? fullName;
}
