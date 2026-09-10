export type AppPermissions = {
  canAccess: boolean;
  canViewAll: boolean;
  canManage: boolean;
  branches: string[];
  canCreateInvoiceIssuance: boolean;
  canProcessInvoiceIssuance: boolean;
  canCreateRawMaterial: boolean;
  canProcessRawMaterial: boolean;
  /** Effective permission codes from the host (empty when superadmin). */
  codes: ReadonlySet<string>;
  isSuperadmin: boolean;
};

const CREATE_SUFFIX = /^my-requests\..+\.create$/;
const PROCESS_SUFFIX = /^my-requests\..+\.process$/;

export function buildAccessFromPermissions(
  permissions: string[] | undefined,
  isSuperadmin = false,
): AppPermissions {
  const set = new Set((permissions || []).map((p) => p.trim()).filter(Boolean));
  if (isSuperadmin) {
    return {
      canAccess: true,
      canViewAll: true,
      canManage: true,
      branches: ["01", "02"],
      canCreateInvoiceIssuance: true,
      canProcessInvoiceIssuance: true,
      canCreateRawMaterial: true,
      canProcessRawMaterial: true,
      codes: new Set(),
      isSuperadmin: true,
    };
  }
  const branches: string[] = [];
  if (set.has("my-requests.view.filial-01")) branches.push("01");
  if (set.has("my-requests.view.filial-02")) branches.push("02");
  return {
    canAccess: set.has("my-requests.access"),
    canViewAll: set.has("my-requests.view-all"),
    canManage: set.has("my-requests.manage"),
    branches,
    canCreateInvoiceIssuance: set.has("my-requests.invoice-issuance.create"),
    canProcessInvoiceIssuance: set.has("my-requests.invoice-issuance.process"),
    canCreateRawMaterial: set.has("my-requests.raw-material-creation.create"),
    canProcessRawMaterial: set.has("my-requests.raw-material-creation.process"),
    codes: set,
    isSuperadmin: false,
  };
}

export function hasPermissionCode(access: AppPermissions, code: string): boolean {
  return access.isSuperadmin || access.codes.has(code);
}

export function canCreateAnyRequest(access: AppPermissions): boolean {
  if (access.canManage || access.isSuperadmin) return true;
  for (const code of access.codes) {
    if (CREATE_SUFFIX.test(code)) return true;
  }
  return false;
}

/** Upload de artefato / atendimento: process de qualquer tipo vertical ou manage. */
export function canProcessAnyRequest(access: AppPermissions): boolean {
  if (access.canManage || access.isSuperadmin) return true;
  for (const code of access.codes) {
    if (PROCESS_SUFFIX.test(code)) return true;
  }
  return false;
}

/**
 * Alinha à API (`ListWorkQueueRequestsUseCase`): fila só com process de algum tipo,
 * view-all ou manage — não basta `my-requests.access`.
 */
export function canAccessWorkQueue(access: AppPermissions): boolean {
  return (
    access.canManage ||
    access.canViewAll ||
    access.isSuperadmin ||
    canProcessAnyRequest(access)
  );
}

/** Prefixo canônico do tipo (`permission_prefix` da API) → `{prefix}.create`. */
export function canCreateRequestType(
  access: AppPermissions,
  permissionPrefix: string | null | undefined,
  typeCode?: string | null,
): boolean {
  if (access.canManage || access.isSuperadmin) return true;
  const prefix = String(permissionPrefix || (typeCode ? `my-requests.${typeCode}` : ""))
    .trim()
    .replace(/\.+$/, "");
  if (!prefix) return false;
  return hasPermissionCode(access, `${prefix}.create`);
}
