// portal/src/ui/admin/manifest/manifestUtils.ts

import type {
  LocalError,
  ManifestPermission,
  ManifestRoute,
  ManifestSchema,
  ManifestType,
} from "./manifestTypes";

export function slugifyId(v: string) {
  return (v || "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

export function normalizeBasePath(v: string) {
  if (!v) return "";
  let s = v.trim();
  if (!s.startsWith("/")) s = `/${s}`;
  return s.replace(/\/+$/, "") || "/";
}

export function isSemverStrict(v: string) {
  return /^\d+\.\d+\.\d+$/.test(v.trim());
}

export function bumpPatch(version: string): string {
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(version.trim());
  if (!m) return "1.0.1";
  return `${m[1]}.${m[2]}.${Number(m[3]) + 1}`;
}

export function stripErrorPath(path: string | null | undefined): string {
  if (!path) return "_global";
  return path.replace(/^\$\.?/, "").replace(/^\./, "") || "_global";
}

export function emptyManifestFor(type: ManifestType): ManifestSchema {
  const base: Omit<ManifestSchema, "type" | "entry" | "permissions" | "routes"> = {
    schemaVersion: "1.0.0",
    id: "",
    name: "",
    description: "",
    icon: null,
    version: "1.0.0",
    basePath: "",
  };

  const permissions: ManifestPermission[] = [
    { code: ".access", name: "Acesso", description: "Acesso", module: "" },
  ];

  if (type === "microfrontend") {
    return {
      ...base,
      type,
      entry: "/apps//assets/remoteEntry.js",
      permissions,
      routes: [
        {
          path: "",
          label: "Dashboard",
          permission: ".access",
          icon: "layout-dashboard",
          showInMenu: true,
          order: 1,
        },
      ],
      ui: { renderMode: "federated" },
    };
  }

  if (type === "iframe") {
    return {
      ...base,
      type,
      entry: "",
      permissions,
      routes: [
        {
          path: "",
          label: "Abrir",
          permission: ".access",
          icon: "external-link",
          showInMenu: true,
          order: 1,
        },
      ],
      ui: { renderMode: "embedded" },
    };
  }

  return {
    ...base,
    type: "backend-only",
    entry: null,
    permissions,
    routes: [],
    backend: {
      serviceName: "",
      baseUrl: "",
      required: false,
      auth: {
        validateJwt: false,
        audience: "delpi-central",
        issuer: "",
        permissionsHeader: "X-User-Permissions",
      },
    },
  };
}

export function normalizeManifest(input: any): ManifestSchema {
  const type = (input?.type || "microfrontend") as ManifestType;
  const permissions = Array.isArray(input?.permissions) ? input.permissions : [];
  const routes = Array.isArray(input?.routes) ? input.routes : [];

  return {
    schemaVersion: "1.0.0",
    id: String(input?.id || ""),
    name: String(input?.name || ""),
    description: input?.description ?? "",
    icon: input?.icon ?? null,
    version: String(input?.version || "1.0.0"),
    type,
    basePath: String(input?.basePath || input?.base_path || ""),
    entry: input?.entry ?? null,
    permissions: permissions.map((p: any) => ({
      code: String(p?.code || ""),
      name: p?.name ?? null,
      description: p?.description ?? null,
      module: String(p?.module || ""),
    })),
    routes: routes.map((r: any, idx: number) => ({
      path: String(r?.path || ""),
      label: r?.label ?? null,
      permission: r?.permission ?? null,
      icon: r?.icon ?? null,
      entry: r?.entry ?? null,
      order: r?.order ?? idx + 1,
      showInMenu: r?.showInMenu ?? r?.show_in_menu ?? true,
    })),
    backend: input?.backend,
    lifecycle: input?.lifecycle,
    security: input?.security,
    observability: input?.observability,
    ui: input?.ui,
    dependencies: Array.isArray(input?.dependencies) ? input.dependencies : undefined,
  };
}

export function applyIdSuggestions(m: ManifestSchema): ManifestSchema {
  const id = slugifyId(m.id);
  if (!id) return m;

  const permissions = (m.permissions || []).map((p) => {
    const suffix = (p.code || "").includes(".")
      ? (p.code || "").split(".").slice(1).join(".") || "access"
      : (p.code || "access").replace(/^\./, "") || "access";
    return {
      ...p,
      module: id,
      code: `${id}.${suffix}`,
    };
  });

  const firstPerm = permissions[0]?.code || `${id}.access`;
  const basePath = m.basePath?.trim() || `/apps/${id}`;
  const entry =
    m.type === "microfrontend"
      ? m.entry?.includes("/apps/")
        ? `/apps/${id}/assets/remoteEntry.js`
        : m.entry
      : m.entry;

  const routes = (m.routes || []).map((r, idx) => ({
    ...r,
    path: r.path?.trim() || (idx === 0 ? basePath : `${basePath}/route-${idx + 1}`),
    permission: r.permission?.startsWith(".")
      ? firstPerm
      : r.permission || firstPerm,
    order: r.order ?? idx + 1,
  }));

  return {
    ...m,
    id,
    basePath,
    entry,
    permissions,
    routes,
  };
}

export function validateManifestLocal(m: ManifestSchema): LocalError[] {
  const errors: LocalError[] = [];

  if (!m.id.trim()) errors.push({ path: "id", message: "id é obrigatório" });
  if (!m.name.trim()) errors.push({ path: "name", message: "name é obrigatório" });
  if (!m.version.trim()) errors.push({ path: "version", message: "version é obrigatório" });
  else if (!isSemverStrict(m.version)) {
    errors.push({ path: "version", message: "version deve ser SemVer (ex: 1.0.0)" });
  }
  if (!m.basePath.trim()) errors.push({ path: "basePath", message: "basePath é obrigatório" });
  if (!m.icon) errors.push({ path: "icon", message: "Ícone do app é obrigatório" });

  if (m.type === "microfrontend" && !String(m.entry || "").trim()) {
    errors.push({ path: "entry", message: "entry é obrigatório para microfrontend" });
  }

  if (!Array.isArray(m.permissions) || m.permissions.length === 0) {
    errors.push({ path: "permissions", message: "permissions deve ter ao menos 1 item" });
  } else {
    const module = m.id.trim() || "module";
    m.permissions.forEach((p, idx) => {
      if (!p.code.trim()) {
        errors.push({ path: `permissions[${idx}].code`, message: "code é obrigatório" });
      } else if (!p.code.includes(".")) {
        errors.push({
          path: `permissions[${idx}].code`,
          message: "code deve conter '.' (ex: crm.access)",
        });
      }
      if (!(p.module || module).trim()) {
        errors.push({ path: `permissions[${idx}].module`, message: "module é obrigatório" });
      }
      if (!String(p.name || "").trim()) {
        errors.push({ path: `permissions[${idx}].name`, message: "name é obrigatório" });
      }
    });
    const codes = m.permissions.map((p) => p.code.trim()).filter(Boolean);
    const dup = codes.find((c, i) => codes.indexOf(c) !== i);
    if (dup) {
      errors.push({ path: "permissions", message: `permissions contém code duplicado: ${dup}` });
    }
  }

  if (m.type === "backend-only") {
    if (Array.isArray(m.routes) && m.routes.length > 0) {
      errors.push({
        path: "routes",
        message: "plugins backend-only não devem declarar routes",
      });
    }
  } else if (!Array.isArray(m.routes) || m.routes.length === 0) {
    errors.push({ path: "routes", message: "routes deve ter ao menos 1 item" });
  } else {
    m.routes.forEach((r, idx) => {
      if (!String(r.path || "").trim()) {
        errors.push({ path: `routes[${idx}].path`, message: "path é obrigatório" });
      }
      if (!String(r.label || "").trim()) {
        errors.push({ path: `routes[${idx}].label`, message: "label é obrigatório" });
      }
      if (r.order == null || Number.isNaN(Number(r.order))) {
        errors.push({ path: `routes[${idx}].order`, message: "order é obrigatório" });
      }
      if (!r.icon) {
        errors.push({ path: `routes[${idx}].icon`, message: "ícone é obrigatório" });
      }
      const perm = String(r.permission || "").trim();
      if (perm) {
        const exists = m.permissions.some((p) => p.code.trim() === perm);
        if (!exists) {
          errors.push({
            path: `routes[${idx}].permission`,
            message: `permission não existe em permissions: ${perm}`,
          });
        }
      }
    });
  }

  return errors;
}

export type StructuralDelta = {
  isStructural: boolean;
  addedPermCodes: string[];
  removedPermCodes: string[];
  addedRoutePaths: string[];
  removedRoutePaths: string[];
  basePathChanged: boolean;
  typeChanged: boolean;
};

export function computeStructuralDelta(
  baseline: ManifestSchema | null,
  draft: ManifestSchema
): StructuralDelta {
  if (!baseline) {
    return {
      isStructural: true,
      addedPermCodes: draft.permissions.map((p) => p.code).filter(Boolean),
      removedPermCodes: [],
      addedRoutePaths: draft.routes.map((r) => r.path).filter(Boolean),
      removedRoutePaths: [],
      basePathChanged: false,
      typeChanged: false,
    };
  }

  const basePerms = new Set(baseline.permissions.map((p) => p.code.trim()).filter(Boolean));
  const draftPerms = new Set(draft.permissions.map((p) => p.code.trim()).filter(Boolean));
  const baseRoutes = new Set(baseline.routes.map((r) => r.path.trim()).filter(Boolean));
  const draftRoutes = new Set(draft.routes.map((r) => r.path.trim()).filter(Boolean));

  const addedPermCodes = [...draftPerms].filter((c) => !basePerms.has(c));
  const removedPermCodes = [...basePerms].filter((c) => !draftPerms.has(c));
  const addedRoutePaths = [...draftRoutes].filter((p) => !baseRoutes.has(p));
  const removedRoutePaths = [...baseRoutes].filter((p) => !draftRoutes.has(p));
  const basePathChanged =
    normalizeBasePath(baseline.basePath) !== normalizeBasePath(draft.basePath);
  const typeChanged = baseline.type !== draft.type;

  const isStructural =
    addedPermCodes.length > 0 ||
    removedPermCodes.length > 0 ||
    addedRoutePaths.length > 0 ||
    removedRoutePaths.length > 0 ||
    basePathChanged ||
    typeChanged ||
    baseline.version !== draft.version;

  return {
    isStructural,
    addedPermCodes,
    removedPermCodes,
    addedRoutePaths,
    removedRoutePaths,
    basePathChanged,
    typeChanged,
  };
}

export type ManifestDiff = {
  permissions: { added: string[]; removed: string[]; changed: string[] };
  routes: { added: string[]; removed: string[]; changed: string[] };
  meta: { changed: string[] };
};

export function diffManifest(a: any, b: any): ManifestDiff {
  const aPerms = new Map<string, any>(
    (Array.isArray(a?.permissions) ? a.permissions : []).map((p: any) => [
      String(p.code || ""),
      p,
    ])
  );
  const bPerms = new Map<string, any>(
    (Array.isArray(b?.permissions) ? b.permissions : []).map((p: any) => [
      String(p.code || ""),
      p,
    ])
  );
  const aRoutes = new Map<string, any>(
    (Array.isArray(a?.routes) ? a.routes : []).map((r: any) => [String(r.path || ""), r])
  );
  const bRoutes = new Map<string, any>(
    (Array.isArray(b?.routes) ? b.routes : []).map((r: any) => [String(r.path || ""), r])
  );

  const permAdded = [...bPerms.keys()].filter((k) => k && !aPerms.has(k));
  const permRemoved = [...aPerms.keys()].filter((k) => k && !bPerms.has(k));
  const permChanged = [...bPerms.keys()].filter((k) => {
    if (!k || !aPerms.has(k)) return false;
    return JSON.stringify(aPerms.get(k)) !== JSON.stringify(bPerms.get(k));
  });

  const routeAdded = [...bRoutes.keys()].filter((k) => k && !aRoutes.has(k));
  const routeRemoved = [...aRoutes.keys()].filter((k) => k && !bRoutes.has(k));
  const routeChanged = [...bRoutes.keys()].filter((k) => {
    if (!k || !aRoutes.has(k)) return false;
    return JSON.stringify(aRoutes.get(k)) !== JSON.stringify(bRoutes.get(k));
  });

  const metaKeys = ["name", "description", "icon", "basePath", "entry", "type", "version"];
  const metaChanged = metaKeys.filter((k) => JSON.stringify(a?.[k]) !== JSON.stringify(b?.[k]));

  return {
    permissions: { added: permAdded, removed: permRemoved, changed: permChanged },
    routes: { added: routeAdded, removed: routeRemoved, changed: routeChanged },
    meta: { changed: metaChanged },
  };
}

/**
 * Reordena pelo valor informado e reescreve `order` como 1, 2, 3… — a ordem é
 * posicional, então buracos e saltos só confundem quem edita.
 */
export function normalizeRouteOrders(routes: ManifestRoute[]): ManifestRoute[] {
  return routes
    .map((route, index) => {
      const value = Number(route.order);
      return {
        route,
        index,
        sortKey: Number.isFinite(value) ? value : Number.MAX_SAFE_INTEGER,
      };
    })
    .sort((a, b) => a.sortKey - b.sortKey || a.index - b.index)
    .map(({ route }, index) => ({ ...route, order: index + 1 }));
}
