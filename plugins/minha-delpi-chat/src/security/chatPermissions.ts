export const CHAT_PERMISSIONS = {
  ACCESS: "minha-delpi.chat.access",
  ASK: "minha-delpi.chat.ask",
  HISTORY_VIEW: "minha-delpi.chat.history.view",
  ADMIN: "minha-delpi.chat.admin",
  KNOWLEDGE_MANAGE: "minha-delpi.chat.knowledge.manage",
  TOOLS_USE: "minha-delpi.chat.tools.use",
  TOOLS_MANAGE: "minha-delpi.chat.tools.manage",
} as const;

export type ChatPermission =
  (typeof CHAT_PERMISSIONS)[keyof typeof CHAT_PERMISSIONS];

type JwtPayload = {
  permissions?: string[];
  scope?: string;
  roles?: string[];
  role?: string;
  is_superadmin?: boolean;
  isSuperAdmin?: boolean;
  superadmin?: boolean;
  user?: {
    is_superadmin?: boolean;
    isSuperAdmin?: boolean;
    role?: string;
    roles?: string[];
  };
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

    return JSON.parse(atob(padded)) as JwtPayload;
  } catch {
    return null;
  }
}

function isElevatedChatAdmin(payload: JwtPayload | null): boolean {
  if (!payload) {
    return false;
  }

  const roles = new Set<string>();

  for (const role of payload.roles ?? []) {
    roles.add(role);
  }

  if (payload.role) {
    roles.add(payload.role);
  }

  for (const role of payload.user?.roles ?? []) {
    roles.add(role);
  }

  if (payload.user?.role) {
    roles.add(payload.user.role);
  }

  for (const role of payload.realm_access?.roles ?? []) {
    roles.add(role);
  }

  for (const access of Object.values(payload.resource_access ?? {})) {
    for (const role of access.roles ?? []) {
      roles.add(role);
    }
  }

  const normalizedRoles = Array.from(roles).map((role) =>
    role.toLowerCase().replace(/[\s_-]+/g, ""),
  );

  return (
    payload.is_superadmin === true ||
    payload.isSuperAdmin === true ||
    payload.superadmin === true ||
    payload.user?.is_superadmin === true ||
    payload.user?.isSuperAdmin === true ||
    normalizedRoles.some((role) =>
      ["superadmin", "superadministrador", "platformadmin", "admin"].includes(role),
    )
  );
}

function collectTokenPermissions(payload: JwtPayload | null): Set<string> {
  const permissions = new Set<string>();

  if (!payload) {
    return permissions;
  }

  for (const permission of payload.permissions ?? []) {
    permissions.add(permission);
  }

  for (const scope of payload.scope?.split(" ") ?? []) {
    if (scope.trim()) {
      permissions.add(scope.trim());
    }
  }

  for (const role of payload.realm_access?.roles ?? []) {
    permissions.add(role);
  }

  for (const access of Object.values(payload.resource_access ?? {})) {
    for (const role of access.roles ?? []) {
      permissions.add(role);
    }
  }

  return permissions;
}

export async function getCurrentChatPermissions(
  getAccessToken?: () =>
    | string
    | undefined
    | null
    | Promise<string | undefined | null>,
): Promise<Set<string>> {
  const token = await getAccessToken?.();

  if (!token) {
    return new Set();
  }

  return collectTokenPermissions(decodeJwtPayload(token));
}

export async function userHasChatPermission(
  permission: ChatPermission,
  getAccessToken?: () =>
    | string
    | undefined
    | null
    | Promise<string | undefined | null>,
): Promise<boolean> {
  const token = await getAccessToken?.();

  if (!token) {
    return false;
  }

  const payload = decodeJwtPayload(token);

  if (isElevatedChatAdmin(payload)) {
    return true;
  }

  const permissions = collectTokenPermissions(payload);

  return permissions.has(permission);
}

export async function userCanManageChatTools(
  getAccessToken?: () =>
    | string
    | undefined
    | null
    | Promise<string | undefined | null>,
): Promise<boolean> {
  return userHasChatPermission(CHAT_PERMISSIONS.TOOLS_MANAGE, getAccessToken);
}

export async function userCanUseChatTools(
  getAccessToken?: () =>
    | string
    | undefined
    | null
    | Promise<string | undefined | null>,
): Promise<boolean> {
  return userHasChatPermission(CHAT_PERMISSIONS.TOOLS_USE, getAccessToken);
}

/** Painel admin (conhecimento, métricas, diretrizes, etc.). */
export async function userCanOpenChatAdmin(
  getAccessToken?: () =>
    | string
    | undefined
    | null
    | Promise<string | undefined | null>,
): Promise<boolean> {
  const checks = await Promise.all([
    userHasChatPermission(CHAT_PERMISSIONS.ADMIN, getAccessToken),
    userHasChatPermission(CHAT_PERMISSIONS.KNOWLEDGE_MANAGE, getAccessToken),
    userHasChatPermission(CHAT_PERMISSIONS.TOOLS_MANAGE, getAccessToken),
  ]);

  return checks.some(Boolean);
}
