/** Apresentação de identidade a partir do access token do host.
 * Uso exclusivamente visual (saudação/avatar e escopo local de
 * favoritos) — nunca autorização. Mesmo padrão de
 * `plugins/minha-delpi-chat/src/utils/authDisplayName.ts`. */

type JwtPayload = {
  sub?: string;
  name?: string;
  given_name?: string;
  preferred_username?: string;
  email?: string;
};

function decodeBase64Url(value: string): string {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(
    normalized.length + ((4 - (normalized.length % 4)) % 4),
    "=",
  );
  return atob(padded);
}

function fixMojibake(value: string): string {
  try {
    return decodeURIComponent(
      value
        .split("")
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`)
        .join(""),
    );
  } catch {
    return value;
  }
}

function cleanName(value: string | undefined): string | null {
  let normalized = value?.trim();
  if (!normalized) return null;
  if (/Ã.|Â./.test(normalized)) normalized = fixMojibake(normalized);
  if (normalized.includes("@")) return normalized.split("@")[0] || null;
  return normalized;
}

function readPayload(token: string | null | undefined): JwtPayload | null {
  if (!token) return null;
  const [, payloadPart] = token.split(".");
  if (!payloadPart) return null;
  try {
    return JSON.parse(decodeBase64Url(payloadPart)) as JwtPayload;
  } catch {
    return null;
  }
}

export function getDisplayNameFromAccessToken(
  token?: string | null,
): string | null {
  const payload = readPayload(token);
  if (!payload) return null;
  return (
    cleanName(payload.name) ||
    cleanName(payload.given_name) ||
    cleanName(payload.preferred_username) ||
    cleanName(payload.email)
  );
}

/** `sub` do JWT — escopo estável para dados locais por identidade.
 * Não é enviado a nenhum serviço nem usado como autorização. */
export function getSubjectFromAccessToken(
  token?: string | null,
): string | null {
  const sub = readPayload(token)?.sub?.trim();
  return sub || null;
}
