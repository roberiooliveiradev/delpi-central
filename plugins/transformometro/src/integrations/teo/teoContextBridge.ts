import {
  resolveTeoPortalContext,
  type TeoPortalContext,
} from "./teoPortalContext";
import {
  readTeoWorkspaceSelection,
  type TeoWorkspaceSelection,
} from "./teoWorkspaceSelection";

export const TEO_CONTEXT_SITE_TOOL_NAME = "get_current_transformometro_context";

export const TEO_CONTEXT_SITE_TOOL_DESCRIPTION =
  "Returns only the current Portal Transforma+ navigation context " +
  "(process_id, instance_id, revision_id, workspace area, canonical path). " +
  "This is not authorization and not domain state — use the TÉO/" +
  "Transformômetro canonical tools (e.g. get_process_context) to retrieve " +
  "actual data.";

export type TeoContextLocationReader = () => {
  pathname: string;
  hash: string;
};

export type TeoWorkspaceSelectionReader = () => TeoWorkspaceSelection | null;

export type TeoContextSiteTool = {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, never>;
    additionalProperties: false;
  };
  annotations: { readOnlyHint: true };
  execute: () => Promise<TeoPortalContext>;
};

type WebModelContextLike = {
  registerTool?: (tool: TeoContextSiteTool, options?: { signal?: AbortSignal }) => unknown;
};

function defaultReadLocation(): { pathname: string; hash: string } {
  if (typeof window === "undefined") return { pathname: "", hash: "" };
  return { pathname: window.location.pathname, hash: window.location.hash };
}

/**
 * Detecta o entry point WebMCP. O draft atual expõe `document.modelContext`;
 * `navigator.modelContext` é o formato legado (Chromium antigo).
 */
export function resolveWebModelContext(): WebModelContextLike | null {
  const doc =
    typeof document !== "undefined"
      ? (document as unknown as { modelContext?: WebModelContextLike }).modelContext
      : undefined;
  if (doc && typeof doc.registerTool === "function") return doc;
  const nav =
    typeof navigator !== "undefined"
      ? (navigator as unknown as { modelContext?: WebModelContextLike }).modelContext
      : undefined;
  if (nav && typeof nav.registerTool === "function") return nav;
  return null;
}

/**
 * Site tool read-only. `execute` resolve a localização no momento da chamada,
 * então navegação entre processo/melhoria/revisão/seção nunca devolve
 * contexto obsoleto.
 */
export function buildTeoContextSiteTool(
  readLocation: TeoContextLocationReader = defaultReadLocation,
  readSelection: TeoWorkspaceSelectionReader = readTeoWorkspaceSelection,
): TeoContextSiteTool {
  return {
    name: TEO_CONTEXT_SITE_TOOL_NAME,
    description: TEO_CONTEXT_SITE_TOOL_DESCRIPTION,
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true },
    execute: async () => {
      const { pathname, hash } = readLocation();
      return resolveTeoPortalContext(pathname, hash, readSelection());
    },
  };
}

let siteToolRegistered = false;
let activeSignal: AbortSignal | null = null;

/** Reseta o guard de registro (testes / remount após abort). */
export function resetTeoContextSiteToolRegistration() {
  siteToolRegistered = false;
  activeSignal = null;
}

/**
 * Registra a site tool WebMCP quando o ambiente suporta (ChatGPT desktop,
 * built-in browser). Retorna false quando não há `modelContext` — o Portal
 * continua funcional e o fallback manual (copiar contexto) cobre o resto.
 */
export function registerTeoContextSiteTool(options?: {
  signal?: AbortSignal;
  modelContext?: WebModelContextLike | null;
}): boolean {
  if (siteToolRegistered) return true;
  const modelContext = options?.modelContext ?? resolveWebModelContext();
  if (!modelContext || typeof modelContext.registerTool !== "function") return false;
  try {
    const signal = options?.signal ?? null;
    modelContext.registerTool(buildTeoContextSiteTool(), {
      signal: signal ?? undefined,
    });
    siteToolRegistered = true;
    activeSignal = signal;
    signal?.addEventListener("abort", () => {
      if (activeSignal === signal) {
        siteToolRegistered = false;
        activeSignal = null;
      }
    });
    return true;
  } catch {
    return false;
  }
}
