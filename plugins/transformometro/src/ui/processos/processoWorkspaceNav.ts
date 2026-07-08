import type { Processo, ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";
import type { MatrizImpactoPonto } from "../../data/api/transformometroMatrixApi";
import { resolveMatrixTreeBadge, type ProcessoWorkspaceMatrixBadge } from "../../content/matrizImpactoLabels";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import { buildInstanciaPath, buildProcessoPath } from "../../utils/routeParser";

export type ProcessoWorkspaceSectionId =
  | "visao-geral"
  | "dados"
  | "mapeamento"
  | "diagrama"
  | "arquivos"
  | "melhorias"
  | "timeline";

export type RevisaoWorkspaceSectionId =
  | "matriz"
  | "vigencia"
  | "mapeamento"
  | "diagrama"
  | "medicao"
  | "investimentos"
  | "recursos"
  | "evidencias";

export type ProcessoWorkspaceNodeKind = "section" | "instancia" | "revisao" | "revisao-section";

export type ProcessoWorkspaceNavNode = {
  id: string;
  kind: ProcessoWorkspaceNodeKind;
  label: string;
  searchText: string;
  href: string;
  depth: number;
  children?: ProcessoWorkspaceNavNode[];
  badge?: string;
  matrixBadge?: ProcessoWorkspaceMatrixBadge;
};

export const PROCESSO_WORKSPACE_SECTIONS: Array<{
  id: ProcessoWorkspaceSectionId;
  label: string;
}> = [
  { id: "visao-geral", label: "Visão geral" },
  { id: "dados", label: "Dados do processo" },
  { id: "mapeamento", label: "Mapeamento" },
  { id: "diagrama", label: "Diagrama macro" },
  { id: "arquivos", label: "Arquivos" },
  { id: "melhorias", label: "Melhorias" },
  { id: "timeline", label: "Linha do tempo" },
];

export const REVISAO_WORKSPACE_SECTIONS: Array<{
  id: RevisaoWorkspaceSectionId;
  label: string;
}> = [
  { id: "matriz", label: "Matriz impacto × esforço" },
  { id: "vigencia", label: "Vigência e identificação" },
  { id: "mapeamento", label: "Mapeamento da revisão" },
  { id: "diagrama", label: "Diagrama da revisão" },
  { id: "medicao", label: "Medição operacional" },
  { id: "investimentos", label: "Investimentos" },
  { id: "recursos", label: "Recursos compartilhados" },
  { id: "evidencias", label: "Evidências" },
];

const SECTION_IDS = new Set<string>(PROCESSO_WORKSPACE_SECTIONS.map((item) => item.id));
const REVISAO_SECTION_IDS = new Set<string>(REVISAO_WORKSPACE_SECTIONS.map((item) => item.id));

export function isProcessoWorkspaceSectionId(value: string): value is ProcessoWorkspaceSectionId {
  return SECTION_IDS.has(value);
}

export function isRevisaoWorkspaceSectionId(value: string): value is RevisaoWorkspaceSectionId {
  return REVISAO_SECTION_IDS.has(value);
}

export function revisaoSectionsForCenario(cenarioTipo?: string | null): Array<{
  id: RevisaoWorkspaceSectionId;
  label: string;
}> {
  const isBaseline = String(cenarioTipo ?? "").toLowerCase() === "baseline";
  return REVISAO_WORKSPACE_SECTIONS.filter((section) => section.id !== "matriz" || !isBaseline);
}

export function defaultRevisaoSection(cenarioTipo?: string | null): RevisaoWorkspaceSectionId {
  const sections = revisaoSectionsForCenario(cenarioTipo);
  return sections[0]?.id ?? "vigencia";
}

export function parseRevisaoSectionFromHash(
  hash: string,
  cenarioTipo?: string | null
): RevisaoWorkspaceSectionId {
  const raw = (hash.startsWith("#") ? hash.slice(1) : hash).trim().toLowerCase();
  const allowed = new Set(revisaoSectionsForCenario(cenarioTipo).map((section) => section.id));
  if (raw && isRevisaoWorkspaceSectionId(raw) && allowed.has(raw)) {
    return raw;
  }
  return defaultRevisaoSection(cenarioTipo);
}

export function buildRevisaoSectionHref(
  processoId: string,
  instanciaId: string,
  revisaoId: string,
  section: RevisaoWorkspaceSectionId,
  cenarioTipo?: string | null
): string {
  const base = buildProcessoPath(processoId, revisaoId, instanciaId);
  if (section === defaultRevisaoSection(cenarioTipo)) return base;
  return `${base}#${section}`;
}

function buildRevisaoSectionNodes(input: {
  processoId: string;
  instanciaId: string;
  revisao: Revisao;
}): ProcessoWorkspaceNavNode[] {
  const { processoId, instanciaId, revisao } = input;
  return revisaoSectionsForCenario(revisao.cenario_tipo).map((section) => ({
    id: `revisao-section:${revisao.revisao_id}:${section.id}`,
    kind: "revisao-section" as const,
    label: section.label,
    searchText: `${section.label} ${revisao.versao_revisao ?? ""} ${revisao.cenario_tipo ?? ""}`.toLowerCase(),
    href: buildRevisaoSectionHref(processoId, instanciaId, revisao.revisao_id, section.id, revisao.cenario_tipo),
    depth: 4,
  }));
}

export function parseProcessoSectionFromHash(hash: string): ProcessoWorkspaceSectionId {
  const raw = (hash.startsWith("#") ? hash.slice(1) : hash).trim().toLowerCase();
  if (!raw || raw === "nova-instancia") return raw === "nova-instancia" ? "melhorias" : "visao-geral";
  return isProcessoWorkspaceSectionId(raw) ? raw : "visao-geral";
}

export function buildProcessoSectionHref(processoId: string, section: ProcessoWorkspaceSectionId): string {
  if (section === "visao-geral") return buildProcessoPath(processoId);
  if (section === "melhorias") return `${buildProcessoPath(processoId)}#melhorias`;
  return `${buildProcessoPath(processoId)}#${section}`;
}

export function instanciaNavLabel(instancia: ProcessoInstancia): string {
  const rotulo = instancia.rotulo_instancia?.trim();
  if (rotulo) return rotulo;
  if (instancia.todas_filiais_ativas) return "Todas as unidades";
  const filial = instancia.codigo_filial ?? instancia.filial_id ?? "";
  const setor = instancia.codigo_setor ?? instancia.setor_id ?? "";
  if (filial && setor) return `${filial} · ${setor}`;
  return filial || setor || "Melhoria";
}

export function buildProcessoWorkspaceTree(input: {
  processo: Processo;
  instancias: ProcessoInstancia[];
  revisoes: Revisao[];
  matrixByRevisaoId?: Record<string, MatrizImpactoPonto>;
}): ProcessoWorkspaceNavNode[] {
  const { processo, instancias, revisoes, matrixByRevisaoId } = input;
  const processoId = processo.processo_id;

  const melhoriaChildren: ProcessoWorkspaceNavNode[] = instancias.map((instancia) => {
    const instanciaRevisoes = revisoes.filter((row) => row.instancia_id === instancia.instancia_id);
    const label = instanciaNavLabel(instancia);
    return {
      id: `instancia:${instancia.instancia_id}`,
      kind: "instancia",
      label,
      searchText: `${label} ${instancia.codigo_filial ?? ""} ${instancia.codigo_setor ?? ""}`.toLowerCase(),
      href: buildInstanciaPath(processoId, instancia.instancia_id),
      depth: 2,
      badge: instanciaRevisoes.length > 0 ? String(instanciaRevisoes.length) : undefined,
      children: instanciaRevisoes.map((revisao) => {
        const revLabel = revisaoDisplayLabel(revisao);
        const matrixBadge = resolveMatrixTreeBadge({
          cenario_tipo: revisao.cenario_tipo,
          ponto: matrixByRevisaoId?.[revisao.revisao_id],
        });
        const defaultSection = defaultRevisaoSection(revisao.cenario_tipo);
        return {
          id: `revisao:${revisao.revisao_id}`,
          kind: "revisao" as const,
          label: revLabel,
          searchText: `${revLabel} ${revisao.versao_revisao ?? ""} ${revisao.cenario_tipo ?? ""}`.toLowerCase(),
          href: buildRevisaoSectionHref(processoId, instancia.instancia_id, revisao.revisao_id, defaultSection),
          depth: 3,
          matrixBadge,
          children: buildRevisaoSectionNodes({
            processoId,
            instanciaId: instancia.instancia_id,
            revisao,
          }),
        };
      }),
    };
  });

  return PROCESSO_WORKSPACE_SECTIONS.map((section) => {
    const base: ProcessoWorkspaceNavNode = {
      id: `section:${section.id}`,
      kind: "section",
      label: section.label,
      searchText: section.label.toLowerCase(),
      href: buildProcessoSectionHref(processoId, section.id),
      depth: 1,
    };

    if (section.id === "melhorias") {
      return {
        ...base,
        badge: instancias.length > 0 ? String(instancias.length) : undefined,
        children: melhoriaChildren,
      };
    }

    return base;
  });
}

export function resolveActiveWorkspaceNodeId(input: {
  view: "processo" | "instancia" | "revisao";
  section?: ProcessoWorkspaceSectionId;
  instanciaId?: string;
  revisaoId?: string;
  revisaoSection?: RevisaoWorkspaceSectionId;
}): string {
  if (input.view === "revisao" && input.revisaoId) {
    if (input.revisaoSection) {
      return `revisao-section:${input.revisaoId}:${input.revisaoSection}`;
    }
    return `revisao:${input.revisaoId}`;
  }
  if (input.view === "instancia" && input.instanciaId) {
    return `instancia:${input.instanciaId}`;
  }
  const section = input.section ?? "visao-geral";
  return `section:${section}`;
}

export function resolveWorkspacePanelKey(input: {
  view: "processo" | "instancia" | "revisao";
  instanciaId?: string;
  revisaoId?: string;
}): string {
  if (input.view === "revisao" && input.revisaoId) {
    return `revisao:${input.revisaoId}`;
  }
  if (input.view === "instancia" && input.instanciaId) {
    return `instancia:${input.instanciaId}`;
  }
  return "processo";
}

export function filterWorkspaceTree(
  nodes: ProcessoWorkspaceNavNode[],
  query: string
): ProcessoWorkspaceNavNode[] {
  const needle = query.trim().toLowerCase();
  if (!needle) return nodes;

  function filterNode(node: ProcessoWorkspaceNavNode): ProcessoWorkspaceNavNode | null {
    const children = (node.children ?? [])
      .map(filterNode)
      .filter((item): item is ProcessoWorkspaceNavNode => item !== null);
    const selfMatch = node.searchText.includes(needle) || node.label.toLowerCase().includes(needle);
    if (!selfMatch && children.length === 0) return null;
    return { ...node, children: children.length > 0 ? children : node.children };
  }

  return nodes.map(filterNode).filter((item): item is ProcessoWorkspaceNavNode => item !== null);
}

export function collectExpandedNodeIds(
  nodes: ProcessoWorkspaceNavNode[],
  activeNodeId: string
): Set<string> {
  const expanded = new Set<string>();

  function walk(node: ProcessoWorkspaceNavNode, ancestors: string[]): boolean {
    const chain = [...ancestors, node.id];
    if (node.id === activeNodeId) {
      chain.forEach((id) => expanded.add(id));
      return true;
    }
    for (const child of node.children ?? []) {
      if (walk(child, chain)) return true;
    }
    return false;
  }

  for (const node of nodes) {
    walk(node, []);
  }

  if (activeNodeId.startsWith("section:") || activeNodeId.startsWith("instancia:")) {
    expanded.add(`section:melhorias`);
  }

  if (activeNodeId.startsWith("revisao-section:") || activeNodeId.startsWith("revisao:")) {
    expanded.add(`section:melhorias`);
  }

  return expanded;
}
