export const GUIAS_PROCEDIMENTOS_ROUTES = {
  home: "/apps/guias-procedimentos",
  department: (slug: string) =>
    `/apps/guias-procedimentos/departamentos/${encodeURIComponent(slug.trim())}`,
  guide: (slug: string) =>
    `/apps/guias-procedimentos/guias/${encodeURIComponent(slug.trim())}`,
  admin: "/apps/guias-procedimentos/admin",
  adminDepartments: "/apps/guias-procedimentos/admin/departamentos",
  adminDepartmentNew: "/apps/guias-procedimentos/admin/departamentos/novo",
  adminDepartmentEdit: (id: string) =>
    `/apps/guias-procedimentos/admin/departamentos/${encodeURIComponent(id)}/editar`,
  adminProcedures: "/apps/guias-procedimentos/admin/procedimentos",
  adminProcedureNew: "/apps/guias-procedimentos/admin/procedimentos/novo",
  adminProcedureEdit: (id: string) =>
    `/apps/guias-procedimentos/admin/procedimentos/${encodeURIComponent(id)}/editar`,
} as const;

export type GuiasProcedimentosView =
  | "home"
  | "department"
  | "detail"
  | "admin-home"
  | "admin-departments"
  | "admin-department-new"
  | "admin-department-edit"
  | "admin-procedures"
  | "admin-procedure-new"
  | "admin-procedure-edit";

export type ParsedGuiasProcedimentosRoute = {
  view: GuiasProcedimentosView;
  slug?: string;
  id?: string;
};

export function normalizeGuiasProcedimentosPath(pathname: string): string {
  if (!pathname) return GUIAS_PROCEDIMENTOS_ROUTES.home;
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function parseGuiasProcedimentosPath(
  pathname: string,
): ParsedGuiasProcedimentosRoute {
  const path = normalizeGuiasProcedimentosPath(pathname);
  const base = "/apps/guias-procedimentos";

  if (path === base || path === `${base}/`) {
    return { view: "home" };
  }

  if (path === `${base}/admin`) {
    return { view: "admin-home" };
  }

  if (path === `${base}/admin/departamentos`) {
    return { view: "admin-departments" };
  }

  if (path === `${base}/admin/departamentos/novo`) {
    return { view: "admin-department-new" };
  }

  const departmentEdit = path.match(
    /^\/apps\/guias-procedimentos\/admin\/departamentos\/([^/]+)\/editar$/,
  );
  if (departmentEdit) {
    return {
      view: "admin-department-edit",
      id: decodeURIComponent(departmentEdit[1]),
    };
  }

  if (path === `${base}/admin/procedimentos`) {
    return { view: "admin-procedures" };
  }

  if (path === `${base}/admin/procedimentos/novo`) {
    return { view: "admin-procedure-new" };
  }

  const procedureEdit = path.match(
    /^\/apps\/guias-procedimentos\/admin\/procedimentos\/([^/]+)\/editar$/,
  );
  if (procedureEdit) {
    return {
      view: "admin-procedure-edit",
      id: decodeURIComponent(procedureEdit[1]),
    };
  }

  const departmentMatch = path.match(
    /^\/apps\/guias-procedimentos\/departamentos\/([^/]+)$/,
  );
  if (departmentMatch) {
    return {
      view: "department",
      slug: decodeURIComponent(departmentMatch[1]),
    };
  }

  const detailMatch = path.match(
    /^\/apps\/guias-procedimentos\/guias\/([^/]+)$/,
  );
  if (detailMatch) {
    return {
      view: "detail",
      slug: decodeURIComponent(detailMatch[1]),
    };
  }

  return { view: "home" };
}

export function isAdminView(view: GuiasProcedimentosView): boolean {
  return view.startsWith("admin");
}
