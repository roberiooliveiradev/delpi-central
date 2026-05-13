type JwtPayload = {
  name?: string;
  given_name?: string;
  preferred_username?: string;
  email?: string;
  sub?: string;
};

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(
    normalized.length + ((4 - (normalized.length % 4)) % 4),
    "=",
  );

  return atob(padded);
}

function cleanName(value: string | undefined): string | null {
  const normalized = value?.trim();

  if (!normalized) {
    return null;
  }

  if (normalized.includes("@")) {
    return normalized.split("@")[0] || null;
  }

  return normalized;
}

export function getDisplayNameFromAccessToken(token?: string | null): string | null {
  if (!token) {
    return null;
  }

  const [, payloadPart] = token.split(".");

  if (!payloadPart) {
    return null;
  }

  try {
    const payload = JSON.parse(decodeBase64Url(payloadPart)) as JwtPayload;

    return (
      cleanName(payload.given_name) ||
      cleanName(payload.name) ||
      cleanName(payload.preferred_username) ||
      cleanName(payload.email) ||
      null
    );
  } catch {
    return null;
  }
}

export function getFirstDisplayName(displayName?: string | null): string | null {
  const normalized = displayName?.trim();

  if (!normalized) {
    return null;
  }

  return normalized.split(/\s+/)[0] || null;
}
