// portal/src/ui/admin/manifest/ManifestEditorPage.tsx

import {
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  FileJson,
  History,
  Image as ImageIcon,
  LayoutGrid,
  Rocket,
  Save,
  Upload,
  Wand2,
} from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient, HttpError } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import { resolveIcon } from "../../../utils/iconResolver";
import {
  Alert,
  Button,
  FormField,
  FormGrid,
  Input,
  PageChrome,
  SegmentedControl,
  Select,
  Spinner,
  Textarea,
} from "../../../ui-kit";
import { IconPickerModal } from "../modals/IconPickerModal";
import { MicrofrontendBaseFields } from "../modals/base/MicrofoentendBaseFields";
import { IframeBaseFields } from "../modals/base/IframeBaseFields";
import { BackendOnlyBaseFields } from "../modals/base/BackendOnlyBaseFields";
import { UIBaseFields } from "../modals/base/UIBaseFields";

import { ManifestPermissionsTable } from "./ManifestPermissionsTable";
import { ManifestRoutesTable } from "./ManifestRoutesTable";
import { ManifestAccessPanel } from "./ManifestAccessPanel";

import type {
  ManifestEditorTab,
  ManifestPermission,
  ManifestRoute,
  ManifestSchema,
  ManifestType,
} from "./manifestTypes";
import {
  applyIdSuggestions,
  bumpPatch,
  computeStructuralDelta,
  emptyManifestFor,
  normalizeBasePath,
  normalizeManifest,
  slugifyId,
  stripErrorPath,
  validateManifestLocal,
} from "./manifestUtils";

import "./ManifestEditorPage.css";

/* =========================
   Constantes / tipos locais
========================= */

const EDITOR_MODE_KEY = "delpi.manifest.editorMode";

type EditorMode = "form" | "json";

type BackendErrorItem = {
  code?: string;
  message: string;
  path: string;
};

type IconPickerState =
  | { open: false }
  | { open: true; kind: "app" }
  | { open: true; kind: "route"; routeIndex: number };

const TAB_LABELS: Record<ManifestEditorTab, string> = {
  base: "Base",
  ui: "Interface",
  backend: "Backend",
  permissions: "Permissões",
  routes: "Rotas",
  access: "Acesso",
  preview: "Preview",
};

const ALL_TABS: ManifestEditorTab[] = [
  "base",
  "ui",
  "backend",
  "permissions",
  "routes",
  "access",
  "preview",
];

const TYPE_LABELS: Record<ManifestType, string> = {
  microfrontend: "Microfrontend (Module Federation / embedded)",
  iframe: "Iframe (aplicação externa)",
  "backend-only": "Backend-only (sem interface)",
};

/* =========================
   Utilitários puros
========================= */

function renderLucideIcon(kebab?: string | null, size = 18) {
  const Icon = resolveIcon(kebab);
  if (!Icon) return null;
  return <Icon size={size} />;
}

function tabForErrorPath(path: string): ManifestEditorTab {
  if (path.startsWith("permissions")) return "permissions";
  if (path.startsWith("routes")) return "routes";
  if (
    path.startsWith("backend") ||
    path.startsWith("lifecycle") ||
    path.startsWith("security") ||
    path.startsWith("observability")
  ) {
    return "backend";
  }
  if (path.startsWith("ui")) return "ui";
  return "base";
}

function readStoredEditorMode(): EditorMode {
  try {
    const raw = window.localStorage.getItem(EDITOR_MODE_KEY);
    return raw === "json" ? "json" : "form";
  } catch {
    return "form";
  }
}

function downloadJson(filename: string, payload: unknown) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function permissionSuffixFromPath(path: string, basePath: string) {
  const rest = path.startsWith(basePath) ? path.slice(basePath.length) : path;
  const slug = slugifyId(rest.replace(/^\/+/, "").replace(/\//g, "-"));
  return slug || "access";
}

/* =========================
   Página
========================= */

export function ManifestEditorPage() {
  const { appId } = useParams<{ appId: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { getAccessToken } = useContext(AuthContext);

  const api = useMemo(
    () => new AdminApi(new ApiClient("", getAccessToken)),
    [getAccessToken]
  );

  const isEdit = Boolean(appId);
  const focusCode = searchParams.get("focusCode");

  const [manifest, setManifest] = useState<ManifestSchema>(() =>
    emptyManifestFor("microfrontend")
  );
  const [baseline, setBaseline] = useState<ManifestSchema | null>(null);

  const [loading, setLoading] = useState(Boolean(appId));
  const [loadError, setLoadError] = useState<string | null>(null);

  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [backendErrors, setBackendErrors] = useState<BackendErrorItem[]>([]);

  const [touched, setTouched] = useState<Set<string>>(() => new Set());
  const [iconPicker, setIconPicker] = useState<IconPickerState>({ open: false });

  const [editorMode, setEditorMode] = useState<EditorMode>(readStoredEditorMode);
  const [jsonDraft, setJsonDraft] = useState("");
  const [jsonError, setJsonError] = useState<string | null>(null);

  const [tab, setTab] = useState<ManifestEditorTab>(() => {
    if (searchParams.get("focusCode")) return "access";
    const fromUrl = searchParams.get("tab") as ManifestEditorTab | null;
    return fromUrl && ALL_TABS.includes(fromUrl) ? fromUrl : "base";
  });

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  /* ---------- carga ---------- */

  useEffect(() => {
    if (!appId) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setLoadError(null);

    api
      .getPluginManifest(appId)
      .then((raw: any) => {
        if (cancelled) return;
        const normalized = normalizeManifest(raw?.manifest ?? raw);
        setManifest(normalized);
        setBaseline(normalized);
      })
      .catch((e: any) => {
        if (!cancelled) {
          setLoadError(e?.message || "Não foi possível carregar o manifesto.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [api, appId]);

  useEffect(() => {
    if (focusCode) setTab("access");
  }, [focusCode]);

  /* ---------- derivados ---------- */

  const computed = useMemo(() => {
    const id = slugifyId(manifest.id);
    const basePath = normalizeBasePath(
      manifest.basePath || (id ? `/apps/${id}` : "")
    );
    const renderMode = manifest.ui?.renderMode ?? "embedded";

    const entry =
      manifest.type === "microfrontend"
        ? renderMode === "federated"
          ? `/apps/${id}/assets/remoteEntry.js`
          : `/apps/${id}/`
        : manifest.entry || "";

    return { id, basePath, entry };
  }, [manifest.id, manifest.basePath, manifest.type, manifest.entry, manifest.ui]);

  const finalManifest = useMemo<ManifestSchema>(() => {
    const id = computed.id || manifest.id;
    const basePath = computed.basePath || manifest.basePath;
    const renderMode = manifest.ui?.renderMode ?? "embedded";

    const permissions: ManifestPermission[] = (manifest.permissions || []).map(
      (p) => {
        let code = (p.code || "").trim();
        if (code.startsWith(".")) code = `${id}${code}`;
        return {
          ...p,
          code,
          // module é sempre o id do app (regra do registro de plugins)
          module: id || slugifyId(p.module || ""),
          name: (p.name ?? "").trim() || code,
          description: p.description ?? null,
        };
      }
    );

    const routes: ManifestRoute[] =
      manifest.type === "backend-only"
        ? []
        : (manifest.routes || []).map((r) => {
            let permission = r.permission ? String(r.permission).trim() : "";
            if (permission.startsWith(".")) permission = `${id}${permission}`;
            return {
              ...r,
              path: (r.path || "").trim(),
              label: r.label ?? null,
              permission: permission || null,
              icon: r.icon ? String(r.icon).trim() : null,
              entry: r.entry ?? null,
              order: r.order ?? null,
              showInMenu: r.showInMenu ?? true,
            };
          });

    return {
      ...manifest,
      schemaVersion: "1.0.0",
      id,
      basePath,
      entry:
        manifest.type === "microfrontend"
          ? renderMode === "federated"
            ? computed.entry
            : manifest.entry ?? computed.entry
          : manifest.type === "backend-only"
          ? null
          : manifest.entry ?? null,
      permissions,
      routes,
      ui:
        manifest.type === "backend-only"
          ? undefined
          : manifest.ui ?? { renderMode: "embedded" },
    };
  }, [manifest, computed]);

  const localErrors = useMemo(
    () => validateManifestLocal(finalManifest),
    [finalManifest]
  );

  const errorsByPath = useMemo(() => {
    const map = new Map<string, string[]>();

    for (const e of localErrors) {
      const arr = map.get(e.path) || [];
      arr.push(e.message);
      map.set(e.path, arr);
    }

    for (const e of backendErrors) {
      const arr = map.get(e.path) || [];
      arr.push(e.message);
      map.set(e.path, arr);
    }

    return map;
  }, [localErrors, backendErrors]);

  const getFieldErrors = useCallback(
    (path: string) => errorsByPath.get(path) || [],
    [errorsByPath]
  );

  const hasErrors = localErrors.length > 0 || backendErrors.length > 0;

  const delta = useMemo(
    () => computeStructuralDelta(baseline, finalManifest),
    [baseline, finalManifest]
  );

  const isStructuralEdit = isEdit && delta.isStructural;

  const payload = useMemo<ManifestSchema>(() => {
    if (
      isStructuralEdit &&
      baseline &&
      finalManifest.version.trim() === baseline.version.trim()
    ) {
      return { ...finalManifest, version: bumpPatch(finalManifest.version) };
    }
    return finalManifest;
  }, [finalManifest, baseline, isStructuralEdit]);

  const isDirty = useMemo(() => {
    if (!isEdit || !baseline) return true;
    return JSON.stringify(baseline) !== JSON.stringify(finalManifest);
  }, [isEdit, baseline, finalManifest]);

  const visibleTabs = useMemo<ManifestEditorTab[]>(() => {
    const tabs: ManifestEditorTab[] = ["base"];
    if (manifest.type === "backend-only") tabs.push("backend");
    else tabs.push("ui");
    tabs.push("permissions");
    if (manifest.type !== "backend-only") tabs.push("routes");
    tabs.push("access", "preview");
    return tabs;
  }, [manifest.type]);

  useEffect(() => {
    if (!visibleTabs.includes(tab)) setTab("base");
  }, [visibleTabs, tab]);

  const tabErrorCount = useCallback(
    (target: ManifestEditorTab) => {
      let count = 0;
      for (const [path, messages] of errorsByPath.entries()) {
        if (tabForErrorPath(path) === target) count += messages.length;
      }
      return count;
    },
    [errorsByPath]
  );

  /* ---------- mutadores ---------- */

  const clearBackendErrors = useCallback(() => {
    setBackendErrors((prev) => (prev.length ? [] : prev));
    setSaveError(null);
  }, []);

  const setBase = useCallback(
    (patch: Record<string, unknown>) => {
      clearBackendErrors();
      setManifest((prev) => ({ ...prev, ...(patch as Partial<ManifestSchema>) }));
    },
    [clearBackendErrors]
  );

  const markTouched = useCallback((path: string) => {
    setTouched((prev) => {
      if (prev.has(path)) return prev;
      const next = new Set(prev);
      next.add(path);
      return next;
    });
  }, []);

  const isTouched = useCallback((path: string) => touched.has(path), [touched]);

  const changeTab = useCallback(
    (next: ManifestEditorTab) => {
      setTab(next);
      const params = new URLSearchParams(searchParams);
      params.set("tab", next);
      if (next !== "access") params.delete("focusCode");
      setSearchParams(params, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  const changeType = useCallback(
    (nextType: ManifestType) => {
      clearBackendErrors();
      setManifest((prev) => {
        if (isEdit) return { ...prev, type: nextType };
        const template = emptyManifestFor(nextType);
        return {
          ...template,
          id: prev.id,
          name: prev.name,
          description: prev.description,
          icon: prev.icon,
          version: prev.version,
          basePath: prev.basePath,
        };
      });
    },
    [clearBackendErrors, isEdit]
  );

  const handlePickIcon = useCallback(
    (icon: string | null) => {
      setIconPicker((state) => {
        if (!state.open) return { open: false };
        if (state.kind === "app") {
          setManifest((prev) => ({ ...prev, icon }));
        } else {
          const routeIndex = state.routeIndex;
          setManifest((prev) => ({
            ...prev,
            routes: (prev.routes || []).map((r, i) =>
              i === routeIndex ? { ...r, icon } : r
            ),
          }));
        }
        return { open: false };
      });
      clearBackendErrors();
    },
    [clearBackendErrors]
  );

  const iconPickerValue = useMemo(() => {
    if (!iconPicker.open) return null;
    if (iconPicker.kind === "app") return manifest.icon ?? null;
    return manifest.routes?.[iconPicker.routeIndex]?.icon ?? null;
  }, [iconPicker, manifest.icon, manifest.routes]);

  const handleApplySuggestions = useCallback(() => {
    clearBackendErrors();
    setManifest((prev) => applyIdSuggestions(prev));
  }, [clearBackendErrors]);

  const handleCreatePermFromRoute = useCallback(
    (route: ManifestRoute) => {
      clearBackendErrors();
      setManifest((prev) => {
        const id = slugifyId(prev.id) || "app";
        const suffix = permissionSuffixFromPath(
          route.path || "",
          normalizeBasePath(prev.basePath || "")
        );
        const code = `${id}.${suffix}`;
        if ((prev.permissions || []).some((p) => p.code === code)) return prev;
        return {
          ...prev,
          permissions: [
            ...(prev.permissions || []),
            {
              code,
              name: route.label || suffix,
              description: `Acesso a ${route.label || route.path}`,
              module: id,
            },
          ],
          routes: (prev.routes || []).map((r) =>
            r === route || r.path === route.path ? { ...r, permission: code } : r
          ),
        };
      });
    },
    [clearBackendErrors]
  );

  /* ---------- modo JSON ---------- */

  const switchEditorMode = useCallback(
    (mode: EditorMode) => {
      if (mode === "json") {
        setJsonDraft(JSON.stringify(finalManifest, null, 2));
        setJsonError(null);
      }
      setEditorMode(mode);
      try {
        window.localStorage.setItem(EDITOR_MODE_KEY, mode);
      } catch {
        // storage indisponível: modo só nesta sessão
      }
    },
    [finalManifest]
  );

  useEffect(() => {
    if (editorMode === "json" && !jsonDraft) {
      setJsonDraft(JSON.stringify(finalManifest, null, 2));
    }
    // Sincroniza apenas na entrada do modo JSON — edição livre depois.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editorMode]);

  const applyJsonDraft = useCallback(() => {
    try {
      const parsed = JSON.parse(jsonDraft);
      setManifest(normalizeManifest(parsed));
      setJsonError(null);
      clearBackendErrors();
    } catch (e: any) {
      setJsonError(e?.message || "JSON inválido");
    }
  }, [jsonDraft, clearBackendErrors]);

  /* ---------- import / export ---------- */

  const handleExport = useCallback(() => {
    downloadJson(`${finalManifest.id || "manifest"}.json`, finalManifest);
  }, [finalManifest]);

  const handleImportFile = useCallback(
    async (file: File | null | undefined) => {
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        const normalized = normalizeManifest(parsed);
        setManifest(normalized);
        setJsonDraft(JSON.stringify(normalized, null, 2));
        setJsonError(null);
        clearBackendErrors();
      } catch (e: any) {
        setJsonError(e?.message || "Arquivo JSON inválido");
        setSaveError("Não foi possível importar o arquivo: JSON inválido.");
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    },
    [clearBackendErrors]
  );

  /* ---------- salvar ---------- */

  const handleSave = useCallback(async () => {
    setSaveError(null);

    if (localErrors.length > 0) {
      setTouched(new Set(localErrors.map((e) => e.path)));
      const firstTab = tabForErrorPath(localErrors[0].path);
      if (visibleTabs.includes(firstTab)) setTab(firstTab);
      setSaveError(
        `Corrija ${localErrors.length} problema(s) antes de salvar o manifesto.`
      );
      return;
    }

    setSaving(true);
    setBackendErrors([]);

    try {
      if (!isEdit || delta.isStructural) {
        await api.registerManifest(payload);
      } else {
        await api.updatePluginManifest(appId!, payload);
      }
      navigate("/admin?tab=apps");
    } catch (e: any) {
      if (e instanceof HttpError) {
        if (Array.isArray(e.errors) && e.errors.length > 0) {
          const mapped = e.errors.map((it) => ({
            code: it.code,
            message: it.message || "Erro",
            path: stripErrorPath(it.path),
          }));
          setBackendErrors(mapped);
          const firstTab = tabForErrorPath(mapped[0].path);
          if (visibleTabs.includes(firstTab)) setTab(firstTab);
        }
        setSaveError(e.message || "Falha ao salvar o manifesto.");
      } else {
        setSaveError(e?.message || "Falha ao salvar o manifesto.");
      }
    } finally {
      setSaving(false);
    }
  }, [
    api,
    appId,
    delta.isStructural,
    isEdit,
    localErrors,
    navigate,
    payload,
    visibleTabs,
  ]);

  /* ---------- render ---------- */

  const globalErrors = errorsByPath.get("_global") || [];

  const saveLabel = !isEdit
    ? "Registrar aplicação"
    : isStructuralEdit
    ? "Publicar nova versão"
    : "Salvar alterações";

  const SaveIcon = isEdit && !isStructuralEdit ? Save : Rocket;

  if (loading) {
    return (
      <div className="manifest-editor-page">
        <Spinner label="Carregando manifesto…" />
      </div>
    );
  }

  const tabItems = visibleTabs.map((t) => ({
    id: t,
    label: TAB_LABELS[t],
    errorCount: tabErrorCount(t),
  }));

  return (
    <PageChrome
      className="manifest-editor-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Aplicações", onClick: () => navigate("/admin?tab=apps") },
        { label: "Manifesto" },
      ]}
      title={
        isEdit
          ? `Manifesto · ${manifest.name || appId}`
          : "Registrar nova aplicação"
      }
      leading={
        <>
          <Button
            variant="secondary"
            size="sm"
            className="manifest-back-btn"
            onClick={() => navigate("/admin?tab=apps")}
            title="Voltar para Aplicações"
            icon={<ArrowLeft size={16} />}
          />
          <span className="manifest-editor-page__app-icon">
            {renderLucideIcon(manifest.icon, 22) || <LayoutGrid size={22} />}
          </span>
        </>
      }
      subtitle={
        <>
          <code>{finalManifest.id || "sem-id"}</code>
          <span aria-hidden="true">·</span>
          <code>v{payload.version}</code>
          <span aria-hidden="true">·</span>
          {TYPE_LABELS[manifest.type]}
        </>
      }
      actions={
        <>
          <SegmentedControl
            options={[
              { value: "form", label: "Formulário" },
              { value: "json", label: "JSON" },
            ]}
            value={editorMode}
            onChange={(mode) => switchEditorMode(mode)}
            aria-label="Modo do editor"
          />
          <Button
            variant="secondary"
            size="sm"
            icon={<Wand2 size={15} />}
            onClick={handleApplySuggestions}
          >
            Aplicar sugestões
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Upload size={15} />}
            onClick={() => fileInputRef.current?.click()}
          >
            Importar
          </Button>
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={15} />}
            onClick={handleExport}
          >
            Exportar
          </Button>
          {isEdit && (
            <Button
              variant="secondary"
              size="sm"
              icon={<History size={15} />}
              onClick={() => navigate(`/admin/apps/${appId}/versions`)}
            >
              Versões
            </Button>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            className="manifest-hidden-input"
            onChange={(e) => handleImportFile(e.target.files?.[0])}
          />
        </>
      }
      tabs={
        editorMode === "form"
          ? {
              items: tabItems,
              value: tab,
              onChange: (id) => changeTab(id as ManifestEditorTab),
            }
          : undefined
      }
      footer={
        <>
          <div className="manifest-editor-status">
            {hasErrors ? (
              <span className="manifest-editor-status__error">
                <AlertTriangle size={15} />
                {localErrors.length + backendErrors.length} problema(s)
              </span>
            ) : (
              <span className="manifest-editor-status__ok">
                <CheckCircle2 size={15} /> Manifesto válido
              </span>
            )}
            <span className="hint">
              {isEdit
                ? isDirty
                  ? isStructuralEdit
                    ? `Mudança estrutural · publicará v${payload.version}`
                    : "Alterações não salvas"
                  : "Sem alterações"
                : "Novo registro"}
            </span>
          </div>
          <div className="manifest-editor-page__footer-actions">
            <Button
              variant="secondary"
              onClick={() => navigate("/admin?tab=apps")}
              disabled={saving}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              disabled={saving || (isEdit && !isDirty)}
              loading={saving}
              icon={!saving ? <SaveIcon size={15} /> : undefined}
            >
              {saving ? "Salvando…" : saveLabel}
            </Button>
          </div>
        </>
      }
    >
      {loadError && <Alert tone="danger">{loadError}</Alert>}
      {saveError && <Alert tone="danger">{saveError}</Alert>}
      {globalErrors.length > 0 && (
        <Alert tone="danger">
          <ul>
            {globalErrors.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </Alert>
      )}

      {isEdit && isStructuralEdit && (
        <Alert tone="warning" title="Mudança estrutural detectada.">
          Este manifesto será publicado como <code>v{payload.version}</code>{" "}
          (nova versão), preservando o histórico.
          <ul>
            {delta.typeChanged && <li>Tipo do plugin alterado</li>}
            {delta.basePathChanged && <li>basePath alterado</li>}
            {delta.addedPermCodes.length > 0 && (
              <li>Permissões adicionadas: {delta.addedPermCodes.join(", ")}</li>
            )}
            {delta.removedPermCodes.length > 0 && (
              <li>Permissões removidas: {delta.removedPermCodes.join(", ")}</li>
            )}
            {delta.addedRoutePaths.length > 0 && (
              <li>Rotas adicionadas: {delta.addedRoutePaths.join(", ")}</li>
            )}
            {delta.removedRoutePaths.length > 0 && (
              <li>Rotas removidas: {delta.removedRoutePaths.join(", ")}</li>
            )}
          </ul>
        </Alert>
      )}

      {isEdit && !isStructuralEdit && isDirty && (
        <Alert tone="info">
          Alterações cosméticas (nome, descrição, rótulos): serão aplicadas na
          versão atual sem publicar nova versão.
        </Alert>
      )}

      {editorMode === "json" ? (
        <section className="manifest-json-editor">
          <div className="manifest-editor-toolbar">
            <span className="hint">
              Edite o manifesto completo. «Aplicar JSON» valida e devolve ao
              formulário.
            </span>
            <div className="manifest-editor-toolbar__actions">
              <Button
                variant="primary"
                size="sm"
                icon={<FileJson size={15} />}
                onClick={applyJsonDraft}
              >
                Aplicar JSON
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setJsonDraft(JSON.stringify(finalManifest, null, 2));
                  setJsonError(null);
                }}
              >
                Recarregar do formulário
              </Button>
            </div>
          </div>

          {jsonError && <Alert tone="danger">{jsonError}</Alert>}

          <Textarea
            className="manifest-json-textarea"
            mono
            spellCheck={false}
            rows={24}
            value={jsonDraft}
            onChange={(e) => setJsonDraft(e.target.value)}
          />
        </section>
      ) : (
        <section className="manifest-editor-panel" role="tabpanel">
          {tab === "base" && (
            <>
              <FormGrid columns={2}>
                <FormField
                  label="ID da aplicação"
                  required
                  htmlFor="manifest-id"
                  error={isTouched("id") ? getFieldErrors("id") : []}
                >
                  <Input
                    id="manifest-id"
                    mono
                    value={manifest.id}
                    disabled={isEdit}
                    onBlur={() => markTouched("id")}
                    onChange={(e) => setBase({ id: slugifyId(e.target.value) })}
                    placeholder="ex: crm"
                  />
                </FormField>

                <FormField
                  label="Nome"
                  required
                  htmlFor="manifest-name"
                  error={isTouched("name") ? getFieldErrors("name") : []}
                >
                  <Input
                    id="manifest-name"
                    value={manifest.name}
                    onBlur={() => markTouched("name")}
                    onChange={(e) => setBase({ name: e.target.value })}
                    placeholder="ex: CRM Comercial"
                  />
                </FormField>

                <FormField
                  label="Versão (SemVer)"
                  required
                  htmlFor="manifest-version"
                  error={isTouched("version") ? getFieldErrors("version") : []}
                >
                  <Input
                    id="manifest-version"
                    mono
                    value={manifest.version}
                    onBlur={() => markTouched("version")}
                    onChange={(e) => setBase({ version: e.target.value })}
                    placeholder="1.0.0"
                  />
                </FormField>

                <FormField label="Tipo" htmlFor="manifest-type">
                  <Select
                    id="manifest-type"
                    value={manifest.type}
                    onChange={(next) => changeType(next as ManifestType)}
                    options={(Object.keys(TYPE_LABELS) as ManifestType[]).map(
                      (t) => ({ value: t, label: TYPE_LABELS[t] }),
                    )}
                  />
                </FormField>

                <div className="portal-ui-form-grid__full">
                  <FormField
                    label="basePath"
                    required
                    htmlFor="manifest-base-path"
                    error={isTouched("basePath") ? getFieldErrors("basePath") : []}
                  >
                    <Input
                      id="manifest-base-path"
                      mono
                      value={manifest.basePath}
                      onBlur={() => markTouched("basePath")}
                      onChange={(e) => setBase({ basePath: e.target.value })}
                      placeholder={`/apps/${computed.id || "app-id"}`}
                    />
                  </FormField>
                </div>

                <div className="portal-ui-form-grid__full">
                  <FormField
                    label="Ícone do app"
                    required
                    error={getFieldErrors("icon")}
                  >
                    <div className="manifest-icon-field">
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<ImageIcon size={15} />}
                        onClick={() => setIconPicker({ open: true, kind: "app" })}
                      >
                        Selecionar ícone
                      </Button>
                      {manifest.icon ? (
                        <span className="manifest-icon-field__preview">
                          {renderLucideIcon(manifest.icon, 20)}
                          <code>{manifest.icon}</code>
                        </span>
                      ) : (
                        <span className="hint">Nenhum ícone selecionado</span>
                      )}
                    </div>
                  </FormField>
                </div>

                <div className="portal-ui-form-grid__full">
                  <FormField label="Descrição" htmlFor="manifest-description">
                    <Textarea
                      id="manifest-description"
                      rows={3}
                      value={manifest.description ?? ""}
                      onChange={(e) => setBase({ description: e.target.value })}
                      placeholder="O que esta aplicação faz…"
                    />
                  </FormField>
                </div>
              </FormGrid>

              {manifest.type === "microfrontend" && (
                <MicrofrontendBaseFields
                  manifest={manifest}
                  computed={computed}
                  setBase={setBase}
                  markTouched={markTouched}
                  isTouched={isTouched}
                  getFieldErrors={getFieldErrors}
                  openAppIconPicker={() =>
                    setIconPicker({ open: true, kind: "app" })
                  }
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

              {manifest.type === "backend-only" && (
                <div className="hint">
                  Plugins <code>backend-only</code> não declaram rotas de menu.
                  Configure o serviço na aba <strong>Backend</strong>.
                </div>
              )}
            </>
          )}

          {tab === "ui" && manifest.type !== "backend-only" && (
            <FormGrid columns={2}>
              <UIBaseFields manifest={manifest} setBase={setBase} />
            </FormGrid>
          )}

          {tab === "backend" && manifest.type === "backend-only" && (
            <BackendOnlyBaseFields
              manifest={manifest}
              setBase={setBase}
              errorsByPath={errorsByPath}
            />
          )}

          {tab === "permissions" && (
            <>
              {getFieldErrors("permissions").length > 0 && (
                <Alert tone="danger">
                  <ul>
                    {getFieldErrors("permissions").map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </Alert>
              )}

              <ManifestPermissionsTable
                permissions={manifest.permissions}
                moduleId={computed.id}
                disabled={saving}
                onChange={(next) => setBase({ permissions: next })}
                onWhoUses={
                  isEdit
                    ? (code) => {
                        const params = new URLSearchParams(searchParams);
                        params.set("tab", "access");
                        params.set("focusCode", code);
                        setSearchParams(params, { replace: true });
                        setTab("access");
                      }
                    : undefined
                }
                onGrantToRole={(code) =>
                  navigate(
                    `/admin/roles/new?module=${encodeURIComponent(
                      computed.id,
                    )}&permissionCodes=${encodeURIComponent(code)}`,
                  )
                }
              />
            </>
          )}

          {tab === "routes" && manifest.type !== "backend-only" && (
            <>
              {getFieldErrors("routes").length > 0 && (
                <Alert tone="danger">
                  <ul>
                    {getFieldErrors("routes").map((m, i) => (
                      <li key={i}>{m}</li>
                    ))}
                  </ul>
                </Alert>
              )}

              <ManifestRoutesTable
                routes={manifest.routes}
                permissions={finalManifest.permissions}
                basePath={computed.basePath}
                disabled={saving}
                onChange={(next) => setBase({ routes: next })}
                onPickIcon={(routeIndex) =>
                  setIconPicker({ open: true, kind: "route", routeIndex })
                }
                onCreatePermFromRoute={handleCreatePermFromRoute}
                renderIcon={(kebab) => renderLucideIcon(kebab, 16)}
              />
            </>
          )}

          {tab === "access" && (
            <ManifestAccessPanel
              appId={appId}
              api={api}
              filterCode={focusCode}
              permissionCodes={finalManifest.permissions.map((p) => p.code)}
            />
          )}

          {tab === "preview" && (
            <>
              {hasErrors ? (
                <Alert tone="danger">
                  <ul>
                    {localErrors.map((e, i) => (
                      <li key={`l-${i}`}>
                        <code>{e.path}</code> — {e.message}
                      </li>
                    ))}
                    {backendErrors.map((e, i) => (
                      <li key={`b-${i}`}>
                        <code>{e.path}</code> — {e.message}
                      </li>
                    ))}
                  </ul>
                </Alert>
              ) : (
                <Alert tone="success">Manifesto válido.</Alert>
              )}

              <div className="hint">
                Payload enviado para{" "}
                <code>
                  {!isEdit || delta.isStructural
                    ? "POST /admin/apps/register"
                    : `PUT /admin/apps/${appId}/manifest`}
                </code>
                .
              </div>

              <Textarea
                className="manifest-json-textarea"
                mono
                readOnly
                spellCheck={false}
                rows={24}
                value={JSON.stringify(payload, null, 2)}
              />
            </>
          )}
        </section>
      )}

      <IconPickerModal
        open={iconPicker.open}
        value={iconPickerValue}
        onClose={() => setIconPicker({ open: false })}
        onPick={handlePickIcon}
      />
    </PageChrome>
  );
}

export default ManifestEditorPage;
