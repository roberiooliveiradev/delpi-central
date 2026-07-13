// src/ui/admin/modals/ManifestRegisterModal.tsx

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import "./ManifestRegisterModal.css"
import { Modal } from "../../../components/Modal";
import * as LucideIcons from "lucide-react";
import { IconPickerModal } from "./IconPickerModal";
import { FormField } from "../../../components/FormField";
import { HttpError } from "../../../data/apiClient";

import { MicrofrontendBaseFields } from "./base/MicrofoentendBaseFields";
import { IframeBaseFields } from "./base/IframeBaseFields";
import { BackendOnlyBaseFields } from "./base/BackendOnlyBaseFields";
import { UIBaseFields } from "./base/UIBaseFields";

/* =========================
   Types
========================= */

type ManifestType = "microfrontend" | "iframe" | "backend-only";

type BackendErrorItem = {
  code?: string;
  message: string;
  path?: string | null;
};

type ManifestPermission = {
  code: string;
  name?: string | null;
  description?: string | null;
  module: string;
};

type ManifestRoute = {
  path: string;
  label?: string | null;
  permission?: string | null;
  icon?: string | null; // kebab-case
  entry?: string | null;
  order?: number | null;
  showInMenu?: boolean | null;
};

type ManifestUI = {
  renderMode?: "embedded" | "external" | "federated";
};

type ManifestSchema = {
  schemaVersion: "1.0.0";
  id: string;
  name: string;
  description?: string | null;
  icon?: string | null;
  version: string;
  type: ManifestType;
  basePath: string;
  entry?: string | null;
  permissions: ManifestPermission[];
  routes: ManifestRoute[];

  backend?: any;
  lifecycle?: any;
  security?: any;
  observability?: any;
  ui?: ManifestUI;
};

type Props = {
  open: boolean;
  onClose: () => void;
  onSubmit: (manifest: any) => Promise<void>;
  mode?: "register" | "edit";
  initialManifest?: any;
  title?: string;
};

type Tab = "base" | "ui" | "backend" | "permissions" | "routes" | "preview";

type IconPickerState =
  | { open: false }
  | { open: true; kind: "route"; routeIndex: number }
  | { open: true; kind: "app" };

/* =========================
   Utils (pure)
========================= */

function kebabToPascal(kebab: string) {
  return kebab
    .split("-")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join("");
}

function renderLucideIcon(
  kebab: string | null | undefined,
  size = 18
) {
  if (!kebab) return null;

  const pascal = kebabToPascal(kebab);
  const Icon = (LucideIcons as any)[pascal];

  if (!Icon) return null;

  return <Icon size={size} strokeWidth={1.8} />;
}

function slugifyId(v: string) {
  return (v || "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

function normalizeBasePath(v: string) {
  if (!v) return "";
  let s = v.trim();
  if (!s.startsWith("/")) s = "/" + s;
  if (s.length > 1 && s.endsWith("/")) s = s.slice(0, -1);
  return s;
}

function isSemverLoose(v: string) {
  return /^(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$/.test((v || "").trim());
}

function safeJsonParse(text: string): { ok: true; value: any } | { ok: false; error: string } {
  try {
    const value = JSON.parse(text);
    return { ok: true, value };
  } catch (e: any) {
    return { ok: false, error: e?.message || "JSON inválido" };
  }
}

/** "LayoutDashboard" -> "layout-dashboard" */
function toKebabCase(pascal: string) {
  return pascal
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/_/g, "-")
    .toLowerCase();
}

function emptyManifestFor(type: ManifestType): ManifestSchema {
  const base: Omit<ManifestSchema, "type" | "entry" | "permissions" | "routes"> = {
    schemaVersion: "1.0.0",
    id: "",
    name: "",
    description: "",
    icon: null,
    version: "1.0.0",
    basePath: "",
  };

  const common = {
    permissions: [{ code: ".access", name: null, description: "Acesso", module: "" }] as ManifestPermission[],
  };

  if (type === "microfrontend") {
    return {
      ...base,
      type,
      entry: "/apps//assets/remoteEntry.js",
      ...common,
      routes: [{ path: "", label: "Dashboard", permission: ".access", icon: "layout-dashboard", showInMenu: true }],
      ui: { renderMode: "embedded" },
    };
  }

  if (type === "iframe") {
    return {
      ...base,
      type,
      entry: "https://example.com",
      ...common,
      routes: [{ path: "", label: "Abrir", permission: ".access", icon: "external-link", showInMenu: true }],
      ui: { renderMode: "embedded" },
    };
  }

  return {
    ...base,
    type: "backend-only",
    entry: null,
    ...common,
    routes: [{ path: "", label: "Serviço", permission: ".access", icon: "server", showInMenu: false }],
  };
}

function toManifest(input: any): ManifestSchema {
  const schemaVersion = (input?.schemaVersion || "1.0.0") as "1.0.0";
  const type = (input?.type || "microfrontend") as ManifestType;

  const permissions = Array.isArray(input?.permissions) ? input.permissions : [];
  const routes = Array.isArray(input?.routes) ? input.routes : [];

  return {
    schemaVersion: schemaVersion === "1.0.0" ? "1.0.0" : "1.0.0",
    id: String(input?.id || ""),
    name: String(input?.name || ""),
    description: input?.description ?? null,
    icon: input?.icon ?? null,
    version: String(input?.version || "1.0.0"),
    type,
    basePath: String(input?.basePath || input?.base_path || ""),
    entry: input?.entry ?? null,
    permissions: permissions.map((p: any) => ({
      code: String(p?.code || ""),
      name: p?.name ?? p?.code ?? null,
      description: p?.description ?? null,
      module: String(p?.module || ""),
    })),
    routes: routes.map((r: any) => ({
      path: String(r?.path || ""),
      label: r?.label ?? null,
      permission: r?.permission ?? null,
      icon: r?.icon
        ? (String(r.icon).includes("-")
            ? String(r.icon)
            : toKebabCase(String(r.icon)))
        : null,
      entry: r?.entry ?? null,
      order: r?.order ?? null,
      showInMenu: r?.showInMenu ?? r?.show_in_menu ?? null,
    })),

    backend: input?.backend ?? undefined,
    lifecycle: input?.lifecycle ?? undefined,
    security: input?.security ?? undefined,
    observability: input?.observability ?? undefined,
    ui: input?.ui ?? undefined,
  };
}

function validateManifestLocal(m: ManifestSchema, lucideKebabSet: Set<string>) {
  const errors: { path: string; message: string }[] = [];

  if (m.schemaVersion !== "1.0.0")
    errors.push({ path: "schemaVersion", message: "schemaVersion deve ser 1.0.0" });

  if (!m.id.trim())
    errors.push({ path: "id", message: "id é obrigatório" });

  if (m.id && slugifyId(m.id) !== m.id)
    errors.push({ path: "id", message: "id deve estar no formato slug (ex: crm, helpdesk-glpi)" });

  if (!m.name.trim())
    errors.push({ path: "name", message: "name é obrigatório" });

  if (!m.version.trim())
    errors.push({ path: "version", message: "version é obrigatório" });

  if (m.version && !isSemverLoose(m.version))
    errors.push({ path: "version", message: "version deve ser SemVer (ex: 1.0.0)" });

  if (!m.basePath.trim())
    errors.push({ path: "basePath", message: "basePath é obrigatório" });

  if (m.basePath && normalizeBasePath(m.basePath) !== m.basePath)
    errors.push({ path: "basePath", message: "basePath deve começar com '/' e não terminar com '/'" });

  // 🔥 ICON OBRIGATÓRIO
  const appIcon = (m.icon || "").trim();

  if (!appIcon) {
    errors.push({ path: "icon", message: "Ícone do app é obrigatório" });
  } else if (!lucideKebabSet.has(appIcon)) {
    errors.push({ path: "icon", message: `Ícone Lucide inválido: "${appIcon}"` });
  }

  if (m.type === "microfrontend") {
    const rm = m.ui?.renderMode ?? "embedded";
    const v = String(m.entry || "").trim();

    if (!v) {
      errors.push({ path: "entry", message: "entry é obrigatório para type=microfrontend" });
    } else if (rm === "federated") {
      // federated precisa ser remoteEntry.js
      if (!v.endsWith("/remoteEntry.js") && !v.includes("remoteEntry.js")) {
        errors.push({ path: "entry", message: "Para renderMode=federated, entry deve apontar para remoteEntry.js" });
      }
    } else if (rm === "embedded") {
      // embedded deve ser uma URL interna ou absoluta, mas NÃO remoteEntry
      if (v.includes("remoteEntry.js")) {
        errors.push({ path: "entry", message: "Para renderMode=embedded, entry deve apontar para a raiz do app (ex: /apps/app-id/)" });
      }
      // opcional: garantir que começa com / ou http
      if (!/^\/|^https?:\/\//i.test(v)) {
        errors.push({ path: "entry", message: "Para embedded, entry deve começar com '/' ou 'http(s)://'" });
      }
    }
  }

  if (m.type === "iframe") {

    const hasGlobal = !!String(m.entry || "").trim()

    const hasRouteEntry =
      (m.routes || []).some(r => String(r.entry || "").trim())

    if (!hasGlobal && !hasRouteEntry)
      errors.push({
        path: "entry",
        message: "entry global ou routes[].entry é obrigatório para iframe"
      })
  }

  /* =========================
     Backend-Only
  ========================= */

  if (m.type === "backend-only") {
    if (!m.backend?.serviceName?.trim())
      errors.push({
        path: "backend.serviceName",
        message: "serviceName é obrigatório para backend-only",
      });

    if (!m.backend?.baseUrl?.trim())
      errors.push({
        path: "backend.baseUrl",
        message: "baseUrl é obrigatório para backend-only",
      });

    if (m.backend?.validateJwt) {
      if (!m.backend?.issuer?.trim())
        errors.push({
          path: "backend.issuer",
          message: "issuer é obrigatório quando validateJwt = true",
        });

      if (!m.backend?.audience?.trim())
        errors.push({
          path: "backend.audience",
          message: "audience é obrigatório quando validateJwt = true",
        });
    }
  }

  /* =========================
     UI RENDER IFRAME | MICROFRONTEND
  ========================= */
  if (
    (m.type === "iframe" || m.type === "microfrontend") &&
    m.ui?.renderMode
  ) {
    const allowed =
      m.type === "iframe"
        ? ["embedded", "external"]
        : ["embedded", "federated"];

    if (!allowed.includes(m.ui.renderMode)) {
      errors.push({
        path: "ui.renderMode",
        message: `renderMode inválido para type=${m.type}`,
      });
    }
  }


  /* =========================
     PERMISSIONS
  ========================= */

  if (!Array.isArray(m.permissions) || m.permissions.length === 0) {
    errors.push({ path: "permissions", message: "permissions deve ter ao menos 1 item" });
  } else {
    m.permissions.forEach((p, idx) => {
      if (!p.code.trim())
        errors.push({ path: `permissions[${idx}].code`, message: "code é obrigatório" });

      if (!p.module.trim())
        errors.push({ path: `permissions[${idx}].module`, message: "module é obrigatório" });

      if (!p.name || !String(p.name).trim())
        errors.push({ path: `permissions[${idx}].name`, message: "name é obrigatório" });

      if (p.code && !p.code.includes("."))
        errors.push({ path: `permissions[${idx}].code`, message: "code deve conter '.' (ex: crm.access)" });
    });

    const codes = m.permissions.map((p) => p.code.trim()).filter(Boolean);
    const dup = codes.find((c, i) => codes.indexOf(c) !== i);
    if (dup)
      errors.push({ path: "permissions", message: `permissions contém code duplicado: ${dup}` });
  }

  /* =========================
     ROUTES
  ========================= */

  if (m.type === "backend-only") {
    // Backend-only NÃO deve ter routes
    if (Array.isArray(m.routes) && m.routes.length > 0) {
      errors.push({
        path: "routes",
        message: "plugins backend-only não devem declarar routes",
      });
    }
  } else {
    // Microfrontend e iframe DEVEM ter routes
    if (!Array.isArray(m.routes) || m.routes.length === 0) {
      errors.push({
        path: "routes",
        message: "routes deve ter ao menos 1 item",
      });
    } else {
      m.routes.forEach((r, idx) => {
        if (!r.path.trim())
          errors.push({
            path: `routes[${idx}].path`,
            message: "path é obrigatório",
          });

        if (r.path && !r.path.startsWith("/"))
          errors.push({
            path: `routes[${idx}].path`,
            message: "path deve começar com '/'",
          });

        if (!r.label || !r.label.trim())
          errors.push({
            path: `routes[${idx}].label`,
            message: "label é obrigatório",
          });

        if (r.order === null || r.order === undefined)
          errors.push({
            path: `routes[${idx}].order`,
            message: "order é obrigatório",
          });
        else if (r.order < 0)
          errors.push({
            path: `routes[${idx}].order`,
            message: "order não pode ser negativo",
          });

        const perm = (r.permission || "").trim();
        if (perm) {
          const exists = m.permissions.some(
            (p) => p.code.trim() === perm
          );
          if (!exists)
            errors.push({
              path: `routes[${idx}].permission`,
              message: `permission não existe em permissions: ${perm}`,
            });
        }

        const icon = (r.icon || "").trim();

        if (!icon) {
          errors.push({
            path: `routes[${idx}].icon`,
            message: "ícone é obrigatório",
          });
        } else if (!lucideKebabSet.has(icon)) {
          errors.push({
            path: `routes[${idx}].icon`,
            message: `Ícone Lucide inválido: "${icon}"`,
          });
        }
      });
    }
  }

  return errors;
}

function downloadJson(filename: string, payload: any) {
  const content = JSON.stringify(payload, null, 2);
  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
}

/* =========================
   Main Component
========================= */

export const ManifestRegisterModal = ({
  open,
  onClose,
  onSubmit,
  mode = "register",
  initialManifest,
  title = "Registrar Plugin via Manifesto",
}: Props) => {
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<Tab>("base");

  const [template, setTemplate] = useState<ManifestType>("microfrontend");
  const [manifest, setManifest] = useState<ManifestSchema>(() => emptyManifestFor("microfrontend"));

  const [backendErrors, setBackendErrors] = useState<BackendErrorItem[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [iconPicker, setIconPicker] = useState<IconPickerState>({ open: false });

  const isEdit = mode === "edit";

  const lucideKebabSet = useMemo(() => {
    const pascals = Object.keys(LucideIcons).filter((k) => /^[A-Z][A-Za-z0-9]*$/.test(k));
    return new Set(pascals.map(toKebabCase));
  }, []);

  const [touched, setTouched] = useState<Set<string>>(new Set());

  const markTouched = (path: string) => {
    setTouched((prev) => new Set(prev).add(path));
  };

  const isTouched = (path: string) => touched.has(path);
  
  /* ---------- lifecycle / reset ---------- */

  const resetToRegisterDefaults = useCallback(() => {
    setTemplate("microfrontend");
    setManifest(emptyManifestFor("microfrontend"));
    setTab("base");
    setBackendErrors([]);
    setSubmitError(null);
  }, []);

  useEffect(() => {
    if (!open) return;

    setBackendErrors([]);
    setSubmitError(null);

    if (isEdit && initialManifest) {
      const m = toManifest(initialManifest);
      setTemplate(m.type || "microfrontend");
      setManifest(m);
      setTab("base");
      return;
    }

    if (!isEdit) resetToRegisterDefaults();
  }, [open, isEdit, initialManifest, resetToRegisterDefaults]);

  /* ---------- derived ---------- */

  const computed = useMemo(() => {
    const id = slugifyId(manifest.id);
    const basePath = normalizeBasePath(manifest.basePath || (id ? `/${id}` : ""));

  const renderMode = manifest.ui?.renderMode ?? "embedded";

  const entry =
    manifest.type === "microfrontend"
      ? (renderMode === "federated"
          ? `/apps/${id || ""}/assets/remoteEntry.js`
          : `/apps/${id || ""}/`) // embedded
      : (manifest.entry || "");

    return { id, basePath, entry };
  }, [manifest.id, manifest.basePath, manifest.type, manifest.entry]);

  const finalManifest = useMemo<ManifestSchema>(() => {
    const id = computed.id || manifest.id;
    const basePath = computed.basePath || manifest.basePath;
    const renderMode = manifest.ui?.renderMode ?? "embedded";

    return {
      ...manifest,
      schemaVersion: "1.0.0",
      id,
      basePath,
      entry:
        manifest.type === "microfrontend"
          ? (renderMode === "federated"
              ? computed.entry
              : (manifest.entry ?? computed.entry)) // embedded: respeita o que o usuário configurou
          : manifest.type === "backend-only"
          ? null
          : (manifest.entry ?? null),
      permissions: (manifest.permissions || []).map((p) => {
        const module = slugifyId(p.module || id);
        let code = (p.code || "").trim();
        if (code.startsWith(".")) code = `${id}${code}`;

        // ✅ name obrigatório no DB: fallback para code (ou para o que o usuário preencher)
        const safeName = (p.name ?? "").trim() || code;

        return {
          ...p,
          module,
          code,
          name: safeName,
          description: p.description ?? null,
        };
      }),
      routes: (manifest.routes || []).map((r) => {
        let permission = r.permission ? String(r.permission).trim() : "";

        if (permission.startsWith(".")) permission = `${id}${permission}`;

        return {
          ...r,
          path: (r.path || "").trim(),
          label: r.label ?? null,
          permission: permission ? permission : null,
          icon: r.icon ? String(r.icon).trim() : null,
          entry: r.entry ?? null,
          order: r.order ?? null,
          showInMenu: r.showInMenu ?? null,
        };
      }),
      ui:
      manifest.type === "backend-only"
        ? undefined
        : manifest.ui ?? { renderMode: "embedded" },
    };
  }, [manifest, computed]);

  const localErrors = useMemo(() => validateManifestLocal(finalManifest, lucideKebabSet), [finalManifest, lucideKebabSet]);

  const errorsByPath = useMemo(() => {
    const map = new Map<string, string[]>();

    for (const e of localErrors) {
      const arr = map.get(e.path) || [];
      arr.push(e.message);
      map.set(e.path, arr);
    }

    for (const e of backendErrors) {
      const path = (e.path || "_global").trim();
      const arr = map.get(path) || [];
      arr.push(e.message);
      map.set(path, arr);
    }

    return map;
  }, [localErrors, backendErrors]);

  const getFieldErrors = useCallback((path: string) => errorsByPath.get(path) || [], [errorsByPath]);
  const clearBackendErrors = useCallback(() => setBackendErrors([]), []);

  const hasErrors = localErrors.length > 0 || backendErrors.length > 0;

  /* ---------- state mutators ---------- */

  const setBase = useCallback(
    (patch: Partial<ManifestSchema>) => {
      clearBackendErrors();
      setManifest((prev) => ({ ...prev, ...patch }));
    },
    [clearBackendErrors]
  );

  const updateRoute = useCallback(
    (idx: number, patch: Partial<ManifestRoute>) => {
      clearBackendErrors();
      setManifest((prev) => {
        const next = [...(prev.routes || [])];
        next[idx] = { ...next[idx], ...patch };
        return { ...prev, routes: next };
      });
    },
    [clearBackendErrors]
  );

  const addRoute = useCallback(() => {
    clearBackendErrors();
    setManifest((prev) => ({
      ...prev,
      routes: [
        ...(prev.routes || []),
        {
          path: computed.basePath || "/path",
          label: "",
          permission: prev.permissions?.[0]?.code || null,
          icon: "layout-dashboard",
          showInMenu: true,
        },
      ],
    }));
  }, [clearBackendErrors, computed.basePath]);

  const removeRoute = useCallback(
    (idx: number) => {
      clearBackendErrors();
      setManifest((prev) => {
        const next = [...(prev.routes || [])];
        next.splice(idx, 1);
        return { ...prev, routes: next };
      });
    },
    [clearBackendErrors]
  );

  const updatePermission = useCallback(
    (idx: number, patch: Partial<ManifestPermission>) => {
      clearBackendErrors();
      setManifest((prev) => {
        const next = [...(prev.permissions || [])];
        next[idx] = { ...next[idx], ...patch };
        return { ...prev, permissions: next };
      });
    },
    [clearBackendErrors]
  );

  const addPermission = useCallback(() => {
    clearBackendErrors();
    setManifest((prev) => ({
      ...prev,
      permissions: [
        ...(prev.permissions || []),
        {
          code: `${computed.id || "module"}.new.permission`,
          name: "", 
          description: "",
          module: computed.id || "module",
        },
      ],
    }));
  }, [clearBackendErrors, computed.id]);

  const removePermission = useCallback(
    (idx: number) => {
      clearBackendErrors();
      setManifest((prev) => {
        const next = [...(prev.permissions || [])];
        const removed = next[idx]?.code?.trim();
        next.splice(idx, 1);

        const routes = (prev.routes || []).map((r) =>
          removed && (r.permission || "").trim() === removed ? { ...r, permission: null } : r
        );

        return { ...prev, permissions: next, routes };
      });
    },
    [clearBackendErrors]
  );

  /* ---------- actions ---------- */

  const handleApplySuggestions = useCallback(() => {
    clearBackendErrors();
    setManifest((prev) => {
      const id = slugifyId(prev.id);
      const basePath = normalizeBasePath(prev.basePath || (id ? `/${id}` : ""));

      const renderMode = prev.ui?.renderMode ?? "embedded";

      const entry = (() => {
        // backend-only não usa entry
        if (prev.type === "backend-only") return null;

        // microfrontend: embedded vs federated
        if (prev.type === "microfrontend") {
          if (renderMode === "federated") {
            return `/apps/${id || ""}/assets/remoteEntry.js`;
          }

          // embedded: default para /apps/<id>/
          // (se o usuário já digitou algo válido, respeita)
          const current = String(prev.entry || "").trim();
          if (current) return current;

          return `/apps/${id || ""}/`;
        }

        // iframe
        if (prev.type === "iframe") {
          // external/embedded: URL precisa ser http/https (mas aqui só sugerimos, não inventamos)
          // se estiver vazio, mantemos vazio pra validação acusar
          return prev.entry ?? "";
        }

        return prev.entry ?? "";
      })();

      const permissions = (prev.permissions || []).map((p) => {
        const module = slugifyId(p.module || id);
        let code = p.code || "";
        if (code.startsWith(".")) code = `${id}${code}`;
        if (!code.includes(".") && id) code = `${id}.${code}`;

        const safeName = (p.name ?? "").trim() || code;

        return { ...p, module, code, name: safeName };
      });

      const firstPerm = permissions?.[0]?.code || `${id}.access`;

      const routes = (prev.routes || []).map((r) => {
        let permission = r.permission || "";
        if (permission.startsWith(".")) permission = `${id}${permission}`;

        return {
          ...r,
          path: r.path || basePath,
          permission: permission || firstPerm,
        };
      });

      return {
        ...prev,
        id,
        basePath,
        entry,
        permissions,
        routes,
        ui:
          prev.type === "backend-only"
            ? undefined
            : (prev.ui ?? { renderMode: "embedded" }),
      };
    });
  }, [clearBackendErrors]);

  const setTemplateType = useCallback(
    (t: ManifestType) => {
      setTemplate(t);
      clearBackendErrors();
      setSubmitError(null);
      setTab("base");
      setManifest(emptyManifestFor(t));
    },
    [clearBackendErrors]
  );

  const importFromFile = useCallback(
    async (file: File) => {
      clearBackendErrors();
      setSubmitError(null);

      const text = await file.text();
      const parsed = safeJsonParse(text);

      if (!parsed.ok) {
        setBackendErrors([{ message: `Falha ao importar JSON: ${parsed.error}`, path: "_global" }]);
        setTab("preview");
        return;
      }

      const m = toManifest(parsed.value);
      setTemplate(m.type || "microfrontend");
      setManifest(m);
      setTab("base");
    },
    [clearBackendErrors]
  );

  const handleExport = useCallback(() => {
    const filename = `${finalManifest.id || "manifest"}.json`;
    downloadJson(filename, finalManifest);
  }, [finalManifest]);

  const handleSubmit = useCallback(async () => {
    setSubmitError(null);
    setBackendErrors([]);

    const errs = validateManifestLocal(finalManifest, lucideKebabSet);
    if (errs.length) {
      setTab("preview");
      setSubmitError("Corrija os erros antes de registrar.");
      return;
    }

    try {
      setLoading(true);
      await onSubmit(finalManifest);

      onClose();

      if (!isEdit) resetToRegisterDefaults();
      else setTab("base");
    } 
    
    catch (e: any) {
      if (e instanceof HttpError) {
        if (Array.isArray(e.errors) && e.errors.length > 0) {
          setBackendErrors(
            e.errors.map((it) => ({
              code: it.code,
              message: it.message || "Erro",
              path: it.path || "_global",
            }))
          );

          // Direciona para a aba correta baseado no primeiro erro
          const first = e.errors[0]?.path || "_global";

          if (first.startsWith("permissions")) setTab("permissions");
          else if (first.startsWith("routes")) setTab("routes");
          else if (
            first.startsWith("backend") ||
            first.startsWith("lifecycle") ||
            first.startsWith("security") ||
            first.startsWith("observability") ||
            first.startsWith("ui")
          ) {
            setTab("backend");
          }
          else if (first === "_global") setTab("preview");
          else setTab("base");

          setSubmitError("O backend rejeitou o manifesto. Corrija os campos marcados.");
        } else {
          setSubmitError(e.message || "Erro ao registrar manifesto.");
          setBackendErrors([
            { message: e.message || "Erro desconhecido", path: "_global" },
          ]);
          setTab("preview");
        }

        return;
      }

      // fallback inesperado
      setSubmitError("Erro inesperado.");
      setBackendErrors([{ message: "Erro inesperado.", path: "_global" }]);
      setTab("preview");
    }
    
    finally {
      setLoading(false);
    }
  }, [finalManifest, lucideKebabSet, onSubmit, onClose, isEdit, resetToRegisterDefaults]);

  /* ---------- icon picker ---------- */

  const openRouteIconPicker = useCallback((routeIndex: number) => setIconPicker({ open: true, kind: "route", routeIndex }), []);
  const openAppIconPicker = useCallback(() => setIconPicker({ open: true, kind: "app" }), []);
  const closeIconPicker = useCallback(() => setIconPicker({ open: false }), []);

  /* =========================
     Render
  ========================= */

  return (
    <>
      <Modal
        open={open}
        title={title}
        onClose={onClose}
        size="lg"
        footer={
          <>
            <button onClick={onClose} disabled={loading}>
              Cancelar
            </button>

            <button onClick={() => setTab("preview")} disabled={loading} className="btn-secondary">
              Ver Preview
            </button>

            <button onClick={handleSubmit} disabled={loading || localErrors.length > 0}>
              {loading ? (isEdit ? "Salvando..." : "Registrando...") : isEdit ? "Salvar" : "Registrar"}
            </button>
          </>
        }
      >
        <div className="modal-content-wrapper">
          <div className="row between">
            <div className="row">
              <label className="portal-form-label portal-form-label--inline">
                <span className="sr-only">Template</span>
                <select value={template} onChange={(e) => setTemplateType(e.target.value as ManifestType)} disabled={loading}>
                  <option value="microfrontend">Template: microfrontend</option>
                  <option value="iframe">Template: iframe</option>
                  <option value="backend-only">Template: backend-only</option>
                </select>
              </label>

              <button className="btn-secondary" onClick={() => fileInputRef.current?.click()} disabled={loading}>
                Importar JSON
              </button>

              <button className="btn-secondary" onClick={handleExport} disabled={loading}>
                Exportar JSON
              </button>

              <input
                ref={fileInputRef}
                type="file"
                accept=".json,application/json"
                style={{ display: "none" }}
                onChange={(e) => {
                  const input = e.currentTarget;
                  const file = input.files?.[0];

                  if (file) {
                    importFromFile(file);
                  }

                  // reset imediato, sem await
                  input.value = "";
                }}
              />
            </div>

            <button className="btn-secondary" onClick={handleApplySuggestions} disabled={loading}>
              Aplicar sugestões (ID → basePath/entry/codes)
            </button>
          </div>

          <div className="tabs">
            <button className={tab === "base" ? "active" : ""} onClick={() => setTab("base")}>
              Base
            </button>
             {(manifest.type === "iframe" ||
                manifest.type === "microfrontend") && (
                <button
                  className={tab === "ui" ? "active" : ""}
                  onClick={() => setTab("ui")}
                >
                  UI
                </button>
              )}

              {manifest.type === "backend-only" && (
                <button
                  className={tab === "backend" ? "active" : ""}
                  onClick={() => setTab("backend")}
                >
                  Backend
                </button>
              )}
            <button className={tab === "permissions" ? "active" : ""} onClick={() => setTab("permissions")}>
              Permissões
            </button>
            <button className={tab === "routes" ? "active" : ""} onClick={() => setTab("routes")}>
              Rotas
            </button>
            <button className={tab === "preview" ? "active" : ""} onClick={() => setTab("preview")}>
              Preview JSON
            </button>
          </div>

          {getFieldErrors("_global").length > 0 && (
            <div className="alert danger">
              <strong>Erro:</strong>
              <ul>
                {getFieldErrors("_global").map((msg, i) => (
                  <li key={i}>{msg}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="modal-content-container">
          {/* BASE */}
          {tab === "base" && (
            <>
              <div className="grid-2">
                <FormField
                  label="ID (slug)"
                  required
                  htmlFor="manifest-id"
                  error={isTouched("id") ? getFieldErrors("id") : []}
                >
                  <input
                    value={manifest.id}
                    onBlur={() => markTouched("id")}
                    onChange={(e) => setBase({ id: e.target.value })}
                  />
                </FormField>

                <FormField
                  label="Nome"
                  required
                  htmlFor="manifest-name"
                  error={getFieldErrors("name")}
                >
                  <input
                    value={manifest.name}
                    onBlur={() => markTouched("name")}
                    onChange={(e) => setBase({ name: e.target.value })}
                  />
                </FormField>

                <FormField
                  label="Descrição"
                  htmlFor="manifest-description"
                  error={getFieldErrors("description")}
                >
                  <input
                    value={manifest.description ?? ""}
                    onChange={(e) => setBase({ description: e.target.value })}
                    placeholder="Descrição da aplicação"
                  />
                </FormField>

                <FormField
                  label="Ícone do App (Lucide)"
                  required
                  error={getFieldErrors("icon")}
                >
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => {
                        markTouched("icon");
                        openAppIconPicker();
                      }}
                      disabled={loading}
                    >
                      Selecionar ícone
                    </button>

                    {manifest.icon ? (
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        {renderLucideIcon(manifest.icon, 22)}
                        <code>{manifest.icon}</code>
                      </div>
                    ) : (
                      <span className="dt-muted">Nenhum ícone selecionado</span>
                    )}
                  </div>
                </FormField>

                <FormField
                  label="Versão (SemVer)"
                  required
                  htmlFor="manifest-version"
                  error={isTouched("version") ? getFieldErrors("version") : []}
                >
                  <input
                    value={manifest.version}
                    onBlur={() => markTouched("version")}
                    onChange={(e) => setBase({ version: e.target.value })}
                  />
                </FormField>

                <FormField label="Tipo" htmlFor="manifest-type">
                  <select
                    value={manifest.type}
                    onChange={(e) =>
                      setBase({ type: e.target.value as ManifestType })
                    }
                    disabled={loading}
                  >
                    <option value="microfrontend">microfrontend</option>
                    <option value="iframe">iframe</option>
                    <option value="backend-only">backend-only</option>
                  </select>
                </FormField>

                <FormField
                  label="Base Path"
                  required
                  htmlFor="manifest-basepath"
                  error={isTouched("basePath") ? getFieldErrors("basePath") : []}
                >
                  <>
                    <input
                      value={manifest.basePath}
                      onBlur={() => markTouched("basePath")}
                      onChange={(e) => setBase({ basePath: e.target.value })}
                      placeholder="ex: /crm"
                    />
                    <small>Sugestão: {computed.basePath || "-"}</small>
                  </>
                </FormField>

                {manifest.type === "microfrontend" && (
                  <MicrofrontendBaseFields
                    manifest={manifest}
                    computed={computed}
                    setBase={setBase}
                    markTouched={markTouched}
                    isTouched={isTouched}
                    getFieldErrors={getFieldErrors}
                    openAppIconPicker={openAppIconPicker}
                    renderLucideIcon={renderLucideIcon}
                  />
                )}

                {manifest.type === "iframe" && (
                  <IframeBaseFields
                    manifest={manifest}
                    setBase={setBase}
                    markTouched={markTouched}
                    isTouched={isTouched}
                    getFieldErrors={getFieldErrors}
                  />
                )}
              </div>
            </>
          )}
          {tab === "ui" &&
          (manifest.type === "iframe" ||
            manifest.type === "microfrontend") && (
            <UIBaseFields
              manifest={manifest}
              setBase={setBase}
            />
          )}
          {tab === "backend" && manifest.type === "backend-only" && (
            <>
              <BackendOnlyBaseFields
                manifest={manifest}
                setBase={setBase}
                errorsByPath={errorsByPath}
              />
            </>
          )}
          {/* PERMISSÕES */}
          {tab === "permissions" && (
            <>
              <div className="row between">
                <div className="hint">
                  Permissões são globais. Use prefixo do módulo (ex: <code>{computed.id || "crm"}.access</code>).
                </div>
                <button className="btn-primary" onClick={addPermission} disabled={loading}>
                  Adicionar permissão
                </button>
              </div>

              {getFieldErrors("permissions").length > 0 && (
                <div className="alert">
                  <strong>Permissões:</strong>
                  <ul>
                    {getFieldErrors("permissions").map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="list">
                {manifest.permissions.map((p, idx) => {
                  const codePath = `permissions[${idx}].code`;
                  const namePath = `permissions[${idx}].name`;
                  const modulePath = `permissions[${idx}].module`;

                  return (
                    <div key={idx} className="card">
                      <div className="grid-2">
                        <FormField
                          label="Código"
                          required
                          htmlFor={`perm-code-${idx}`}
                          error={isTouched(codePath) ? getFieldErrors(codePath) : []}
                        >
                          <input
                            value={p.code}
                            onBlur={() => markTouched(codePath)}
                            onChange={(e) => updatePermission(idx, { code: e.target.value })}
                            placeholder="ex: crm.access"
                          />
                        </FormField>

                        <FormField
                          label="Nome (exibido)"
                          htmlFor={`perm-name-${idx}`}
                          error={getFieldErrors(namePath)}
                        >
                          <input
                            value={p.name ?? ""}
                            onBlur={() => markTouched(namePath)}
                            onChange={(e) => updatePermission(idx, { name: e.target.value })}
                            placeholder="ex: Acesso ao CRM"
                          />
                        </FormField>

                        <FormField
                          label="Módulo"
                          required
                          htmlFor={`perm-module-${idx}`}
                          error={getFieldErrors(modulePath)}
                        >
                          <input
                            value={p.module}
                            onBlur={() => markTouched(modulePath)}
                            onChange={(e) => updatePermission(idx, { module: e.target.value })}
                            placeholder={computed.id || "crm"}
                          />
                        </FormField>

                        <FormField
                          label="Descrição"
                          htmlFor={`perm-desc-${idx}`}
                        >
                          <input
                            value={p.description ?? ""}
                            onChange={(e) =>
                              updatePermission(idx, { description: e.target.value })
                            }
                            placeholder="ex: Permite acessar o módulo"
                          />
                        </FormField>
                      </div>

                      <div className="row end">
                        <button className="danger" onClick={() => removePermission(idx)} disabled={loading}>
                          Remover
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* ROTAS */}
          {tab === "routes" && (
            <>
              <div className="row between">
                <div className="hint">
                  Rotas alimentam o menu. <code>permission</code> referencia um <code>permissions[].code</code>.
                </div>
                <button className="btn-primary" onClick={addRoute} disabled={loading}>
                  Adicionar rota
                </button>
              </div>

              {getFieldErrors("routes").length > 0 && (
                <div className="alert">
                  <strong>Rotas:</strong>
                  <ul>
                    {getFieldErrors("routes").map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="list">
                {manifest.routes.map((r, idx) => {
                  const pathPath = `routes[${idx}].path`;
                  const permPath = `routes[${idx}].permission`;
                  const iconPath = `routes[${idx}].icon`;

                  return (
                    <div key={idx} className="card">
                      <div className="grid-2">
                        <FormField
                          label="Path"
                          required
                          htmlFor={`route-path-${idx}`}
                          error={isTouched(pathPath) ? getFieldErrors(pathPath) : []}
                        >
                          <input
                            value={r.path}
                            onBlur={() => markTouched(pathPath)}
                            onChange={(e) => updateRoute(idx, { path: e.target.value })}
                            placeholder="ex: /crm/leads"
                          />
                        </FormField>

                        <FormField
                          label="Label"
                          required
                          htmlFor={`route-label-${idx}`}
                          error={getFieldErrors(`routes[${idx}].label`)}
                        >
                          <input
                            value={r.label ?? ""}
                            onBlur={() => markTouched(`routes[${idx}].label`)}
                            onChange={(e) => updateRoute(idx, { label: e.target.value })}
                            placeholder="ex: Leads"
                          />
                        </FormField>
                        <FormField
                          label="Entry da rota (opcional)"
                          htmlFor={`route-entry-${idx}`}
                        >
                          <>
                            <input
                              value={r.entry ?? ""}
                              onChange={(e) =>
                                updateRoute(idx, { entry: e.target.value || null })
                              }
                              placeholder="URL específica para esta rota"
                            />

                            <small className="hint">
                              Entry efetivo: <code>{r.entry || manifest.entry || "-"}</code>
                            </small>
                          </>
                        </FormField>

                        <FormField
                          label="Permissão"
                          htmlFor={`route-perm-${idx}`}
                          error={getFieldErrors(permPath)}
                        >
                          <select
                            value={r.permission ?? ""}
                            onChange={(e) =>
                              updateRoute(idx, { permission: e.target.value || null })
                            }
                          >
                            <option value="">(Pública / sem permissão)</option>
                            {manifest.permissions.map((p) => (
                              <option key={p.code} value={p.code}>
                                {p.code}
                              </option>
                            ))}
                          </select>
                        </FormField>

                        <FormField
                          label="Ícone (Lucide)"
                          required
                          htmlFor={`route-icon-${idx}`}
                          error={getFieldErrors(iconPath)}
                        >
                          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                            <button
                              type="button"
                              className="btn-secondary"
                              onClick={() => openRouteIconPicker(idx)}
                              disabled={loading}
                            >
                              Selecionar ícone
                            </button>

                            {r.icon ? (
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                {renderLucideIcon(r.icon, 18)}
                                <code>{r.icon}</code>
                              </div>
                            ) : (
                              <span className="dt-muted">(sem ícone)</span>
                            )}
                          </div>
                        </FormField>

                        <FormField label="Mostrar no menu" htmlFor={`route-menu-${idx}`}>
                          <select
                            value={
                              r.showInMenu === null || r.showInMenu === undefined
                                ? ""
                                : r.showInMenu
                                ? "true"
                                : "false"
                            }
                            onChange={(e) => {
                              const v = e.target.value;
                              updateRoute(idx, { showInMenu: v === "" ? null : v === "true" });
                            }}
                          >
                            <option value="">(default)</option>
                            <option value="true">true</option>
                            <option value="false">false</option>
                          </select>
                        </FormField>

                        <FormField
                          label="Ordem"
                          htmlFor={`route-order-${idx}`}
                          error={getFieldErrors(`routes[${idx}].order`)}
                        >
                          <input
                            type="number"
                            value={r.order ?? ""}
                            onBlur={() => markTouched(`routes[${idx}].order`)}
                            onChange={(e) => {
                              const v = e.target.value;
                              updateRoute(idx, { order: v === "" ? null : Number(v) });
                            }}
                            placeholder="ex: 10"
                          />
                        </FormField>
                      </div>

                      <div className="row end">
                        <button className="danger" onClick={() => removeRoute(idx)} disabled={loading}>
                          Remover
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {/* PREVIEW */}
          {tab === "preview" && (
            <>
              {submitError && <div className="alert danger">{submitError}</div>}

              {localErrors.length > 0 && (
                <div className="alert danger">
                  <strong>Erros locais:</strong>
                  <ul>
                    {localErrors.slice(0, 12).map((e, i) => (
                      <li key={i}>
                        <code>{e.path}</code>: {e.message}
                      </li>
                    ))}
                    {localErrors.length > 12 && <li>... e mais {localErrors.length - 12} erro(s)</li>}
                  </ul>
                </div>
              )}

              {backendErrors.length > 0 && (
                <div className="alert danger">
                  <strong>Erros do backend:</strong>
                  <ul>
                    {backendErrors.slice(0, 12).map((e, i) => (
                      <li key={i}>
                        {e.path ? <code>{e.path}</code> : <code>_global</code>}: {e.message}
                        {e.code ? ` (${e.code})` : ""}
                      </li>
                    ))}
                    {backendErrors.length > 12 && <li>... e mais {backendErrors.length - 12} erro(s)</li>}
                  </ul>
                </div>
              )}

              {!hasErrors && <div className="alert success">Manifesto válido ✅</div>}

              <textarea style={{ width: "100%", height: 360, fontFamily: "monospace" }} value={JSON.stringify(finalManifest, null, 2)} readOnly />

              <div className="hint">
                Esse JSON é o payload enviado para <code>/core-api/plugins/register</code>.
              </div>
            </>
          )}
        </div>
        </div>
      </Modal>

      <IconPickerModal
        open={iconPicker.open}
        value={
          iconPicker.open
            ? iconPicker.kind === "app"
              ? manifest.icon ?? null
              : manifest.routes?.[iconPicker.routeIndex]?.icon ?? null
            : null
        }
        onClose={closeIconPicker}
        onPick={(iconKebab) => {
          if (!iconPicker.open) return;

          if (iconPicker.kind === "app") {
            setBase({ icon: iconKebab });
            closeIconPicker();
            return;
          }

          updateRoute(iconPicker.routeIndex, { icon: iconKebab });
          closeIconPicker();
        }}
      />
    </>
  );
};