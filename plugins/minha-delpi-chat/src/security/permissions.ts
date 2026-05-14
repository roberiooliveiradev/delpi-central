const CHAT_TOOLS_MANAGE_PERMISSION = "minha-delpi.chat.tools.manage";

type JwtPayload = {
  permissions?: string[];
  scope?: string;
  realm_access?: {
    roles?: string[];
  };
  resource_access?: Record<string, { roles?: string[] }>;
};

function decodeJwtPayload(token: string): JwtPayload | null {
  const [, payload] = token.split(".");

  if (!payload) {
    return null;
  }

  try {
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(
      normalized.length + ((4 - (normalized.length % 4)) % 4),
      "=",
    );
    const decoded = atob(padded);

    return JSON.parse(decoded) as JwtPayload;
  } catch {
    return null;
  }
}

function collectTokenPermissions(payload: JwtPayload | null): string[] {
  if (!payload) {
    return [];
  }

  const values = new Set<string>();

  for (const permission of payload.permissions ?? []) {
    values.add(permission);
  }

  for (const scope of payload.scope?.split(" ") ?? []) {
    values.add(scope);
  }

  for (const role of payload.realm_access?.roles ?? []) {
    values.add(role);
  }

  for (const access of Object.values(payload.resource_access ?? {})) {
    for (const role of access.roles ?? []) {
      values.add(role);
    }
  }

  return Array.from(values);
}

export async function userCanManageChatTools(
  getAccessToken?: () => Promise<string | null>,
): Promise<boolean> {
  const token = await getAccessToken?.();

  if (!token) {
    return false;
  }

  const payload = decodeJwtPayload(token);
  const permissions = collectTokenPermissions(payload);

  return permissions.includes(CHAT_TOOLS_MANAGE_PERMISSION);
}
