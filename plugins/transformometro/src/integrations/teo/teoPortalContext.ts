import {
  canonicalizeTransformometroPath,
  parseTransformometroPath,
} from "../../utils/routeParser";
import {
  INSTANCIA_WORKSPACE_SECTIONS,
  PROCESSO_WORKSPACE_SECTIONS,
  REVISAO_WORKSPACE_SECTIONS,
  parseInstanciaSectionFromHash,
  parseProcessoSectionFromHash,
  parseRevisaoSectionFromHash,
} from "../../ui/processes/processWorkspaceNav";

export const TEO_PORTAL_CONTEXT_VERSION = "1";
export const TEO_PORTAL_PRODUCT = "transformometro";

/**
 * Contexto identificador de navegação do Portal Transforma+ para handoff
 * ao TÉO (ChatGPT + MCP). É só localização — nunca autorização nem dado
 * de domínio: o TÉO relê o estado real via suas tools canônicas
 * (ex.: `get_process_context`).
 */
export type TeoPortalContext = {
  version: typeof TEO_PORTAL_CONTEXT_VERSION;
  product: typeof TEO_PORTAL_PRODUCT;
  process_id: string | null;
  instance_id: string | null;
  revision_id: string | null;
  /** Seção ativa do workspace (hint conversacional, não policy). */
  area: string | null;
  canonical_path: string;
};

type ProcessWorkspaceView =
  | "processo"
  | "instancia"
  | "revisao"
  | "processoDiagramaEdit"
  | "instanciaDiagramaEdit"
  | "revisaoDiagramaEdit";

const PROCESS_VIEWS = new Set<string>([
  "processo",
  "instancia",
  "revisao",
  "processoDiagramaEdit",
  "instanciaDiagramaEdit",
  "revisaoDiagramaEdit",
]);

function isProcessWorkspaceView(view: string): view is ProcessWorkspaceView {
  return PROCESS_VIEWS.has(view);
}

function resolveArea(view: ProcessWorkspaceView, hash: string): string | null {
  if (view === "processo") return parseProcessoSectionFromHash(hash);
  if (view === "instancia") return parseInstanciaSectionFromHash(hash);
  if (view === "revisao") return parseRevisaoSectionFromHash(hash);
  // Diagrama edit é tela cheia: processo vive sob Mapeamento; melhoria e
  // revisão têm seção "diagrama" própria.
  if (view === "processoDiagramaEdit") return "mapeamento";
  return "diagrama";
}

/**
 * Resolve o contexto a partir da localização atual (pathname + hash).
 * Função pura — derivada da rota, sem fetch de domínio e sem estado.
 */
export function resolveTeoPortalContext(pathname: string, hash: string): TeoPortalContext {
  const canonicalPath = `${canonicalizeTransformometroPath(pathname)}${hash || ""}`;
  const route = parseTransformometroPath(pathname);

  const base: TeoPortalContext = {
    version: TEO_PORTAL_CONTEXT_VERSION,
    product: TEO_PORTAL_PRODUCT,
    process_id: null,
    instance_id: null,
    revision_id: null,
    area: null,
    canonical_path: canonicalPath,
  };

  if (!isProcessWorkspaceView(route.view)) return base;

  base.process_id = route.processoId ?? null;
  base.instance_id = route.instanciaId ?? null;
  base.revision_id = route.revisaoId ?? null;
  base.area = resolveArea(route.view, hash);

  return base;
}

/** Label PT da área ativa, para UI contextual (tooltip/título). */
export function teoAreaLabel(
  view: string | undefined,
  area: string | null,
): string | null {
  if (!area) return null;
  const sections =
    view === "instancia" || view === "instanciaDiagramaEdit"
      ? INSTANCIA_WORKSPACE_SECTIONS
      : view === "revisao" || view === "revisaoDiagramaEdit"
        ? REVISAO_WORKSPACE_SECTIONS
        : PROCESSO_WORKSPACE_SECTIONS;
  return sections.find((section) => section.id === area)?.label ?? null;
}

/** Payload humano e curto para o fallback "copiar contexto". */
export function buildTeoContextClipboardText(context: TeoPortalContext): string {
  const lines = ["TÉO, use este contexto do Portal Transforma+:"];
  if (context.process_id) lines.push(`process_id=${context.process_id}`);
  if (context.instance_id) lines.push(`instance_id=${context.instance_id}`);
  if (context.revision_id) lines.push(`revision_id=${context.revision_id}`);
  if (context.area) lines.push(`area=${context.area}`);
  lines.push(`path=${context.canonical_path}`);
  return lines.join("\n");
}
