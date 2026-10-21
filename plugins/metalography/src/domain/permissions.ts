export const METALOGRAPHY_PERMISSIONS = {
  view: "metalography.view",
  create: "metalography.create",
  edit: "metalography.edit",
  delete: "metalography.delete",
  export: "metalography.export",
} as const;

export type MetalographyPermission = (typeof METALOGRAPHY_PERMISSIONS)[keyof typeof METALOGRAPHY_PERMISSIONS];

export function allows(
  permissions: readonly string[] | undefined,
  isSuperadmin: boolean | undefined,
  code: MetalographyPermission,
): boolean {
  if (isSuperadmin) return true;
  if (!permissions) return true;
  return permissions.includes(code);
}
