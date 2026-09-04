export type AppPermissions = {
  canAccess: boolean;
  canViewAll: boolean;
  canManage: boolean;
  branches: string[];
  canCreateInvoiceIssuance: boolean;
  canProcessInvoiceIssuance: boolean;
  canCreateRawMaterial: boolean;
  canProcessRawMaterial: boolean;
};

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
  };
}

export function canCreateAnyRequest(access: AppPermissions): boolean {
  return (
    access.canManage ||
    access.canCreateInvoiceIssuance ||
    access.canCreateRawMaterial
  );
}

/** Upload de artefato: process de qualquer tipo vertical ou manage. */
export function canProcessAnyRequest(access: AppPermissions): boolean {
  return (
    access.canManage ||
    access.canProcessInvoiceIssuance ||
    access.canProcessRawMaterial
  );
}
