export const TV_TEMPLATES_MANAGE = "tv-dashboard.templates.manage";

export function canManageTemplates(args: {
  permissions?: string[] | null;
  isSuperadmin?: boolean;
  hasPermission?: (code: string) => boolean;
}): boolean {
  if (args.isSuperadmin) return true;
  if (typeof args.hasPermission === "function") {
    return args.hasPermission(TV_TEMPLATES_MANAGE);
  }
  const perms = args.permissions ?? [];
  return perms.includes(TV_TEMPLATES_MANAGE) || perms.includes("tv-dashboard.admin");
}
