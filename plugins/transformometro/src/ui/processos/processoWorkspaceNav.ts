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
  | "priorizacao"
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

export type InstanciaWorkspaceSectionId =
  | "dados"
  | "mapeamento"
  | "contexto"
  | "diagrama"
  | "revisoes";

export type ProcessoWorkspaceNodeKind =
  | "section"
  | "instancia"
  | "instancia-section"
  | "revisao"
  | "revisao-section";

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
  { id: "priorizacao", label: "Priorização (matriz)" },
  { id: "timeline", label: "Linha do tempo" },
];

export const REVISAO_WORKSPACE_SECTIONS: Array<{
  id: RevisaoWorkspaceSectionId;
  label: string;
}> = [
  { id: "vigencia", label: "Vigência e identificação" },
  { id: "matriz", label: "Matriz impacto × esforço" },
  { id: "mapeamento", label: "Mapeamento da revisão" },
  { id: "diagrama", label: "Diagrama da revisão" },
  { id: "medicao", label: "Medição operacional" },
  { id: "investimentos", label: "Investimentos" },
  { id: "recursos", label: "Recursos compartilhados" },
  { id: "evidencias", label: "Evidências" },
];

export const INSTANCIA_WORKSPACE_SECTIONS: Array<{
  id: InstanciaWorkspaceSectionId;
  label: string;
}> = [
  { id: "dados", label: "Instância operacional" },
  { id: "mapeamento", label: "Escopo no mapeamento" },
  { id: "contexto", label: "Contexto operacional" },
  { id: "diagrama", label: "Escopo no diagrama" },
  { id: "revisoes", label: "Revisões" },
];

const SECTION_IDS = new Set<string>(PROCESSO_WORKSPACE_SECTIONS.map((item) => item.id));
const REVISAO_SECTION_IDS = new Set<string>(REVISAO_WORKSPACE_SECTIONS.map((item) => item.id));
const INSTANCIA_SECTION_IDS = new Set<string>(INSTANCIA_WORKSPACE_SECTIONS.map((item) => item.id));

export function isProcessoWorkspaceSectionId(value: string): value is ProcessoWorkspaceSectionId {
  return SECTION_IDS.has(value);
}

export function isRevisaoWorkspaceSectionId(value: string): value is RevisaoWorkspaceSectionId {
  return REVISAO_SECTION_IDS.has(value);
}

export function isInstanciaWorkspaceSectionId(value: string): value is InstanciaWorkspaceSectionId {
  return INSTANCIA_SECTION_IDS.has(value);
}

export function defaultInstanciaSection(): InstanciaWorkspaceSectionId {
  return "dados";
}

export function parseInstanciaSectionFromHash(hash: string): InstanciaWorkspaceSectionId {
  const raw = (hash.startsWith("#") ? hash.slice(1) : hash).trim().toLowerCase();
  if (raw === "nova-revisao") return "revisoes";
  if (raw && isInstanciaWorkspaceSectionId(raw)) return raw;
  return defaultInstanciaSection();
}

export function buildInstanciaSectionHref(
  processoId: string,
  instanciaId: string,
  section: InstanciaWorkspaceSectionId
): string {
  const base = buildInstanciaPath(processoId, instanciaId);
  if (section === defaultInstanciaSection()) return base;
  return `${base}#${section}`;
}

function buildInstanciaSectionNodes(input: {
  processoId: string;
  instancia: ProcessoInstancia;
  revisaoChildren?: ProcessoWorkspaceNavNode[];
}): ProcessoWorkspaceNavNode[] {
  const { processoId, instancia, revisaoChildren = [] } = input;
  return INSTANCIA_WORKSPACE_SECTIONS.map((section) => {
    const base: ProcessoWorkspaceNavNode = {
      id: `instancia-section:${instancia.instancia_id}:${section.id}`,
      kind: "instancia-section" as const,
      label: section.label,
      searchText: `${section.label} ${instanciaNavLabel(instancia)}`.toLowerCase(),
      href: buildInstanciaSectionHref(processoId, instancia.instancia_id, section.id),
      depth: 3,
    };
    if (section.id !== "revisoes") return base;
    return {
      ...base,
      badge: revisaoChildren.length > 0 ? String(revisaoChildren.length) : undefined,
      children: revisaoChildren,
    };
  });
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
    depth: 5,
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
    const instanciaId = String(instancia.instancia_id ?? "").toLowerCase();
    const instanciaRevisoes = revisoes.filter(
      (row) => String(row.instancia_id ?? "").toLowerCase() === instanciaId
    );
    const label = instanciaNavLabel(instancia);
    const revisaoChildren = instanciaRevisoes.map((revisao) => {
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
        depth: 4,
        matrixBadge,
        children: buildRevisaoSectionNodes({
          processoId,
          instanciaId: instancia.instancia_id,
          revisao,
        }),
      };
    });
    return {
      id: `instancia:${instancia.instancia_id}`,
      kind: "instancia",
      label,
      searchText: `${label} ${instancia.codigo_filial ?? ""} ${instancia.codigo_setor ?? ""}`.toLowerCase(),
      href: buildInstanciaSectionHref(processoId, instancia.instancia_id, defaultInstanciaSection()),
      depth: 2,
      badge: instanciaRevisoes.length > 0 ? String(instanciaRevisoes.length) : undefined,
      children: buildInstanciaSectionNodes({
        processoId,
        instancia,
        revisaoChildren,
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
  instanciaSection?: InstanciaWorkspaceSectionId;
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
    const instanciaSection = input.instanciaSection ?? defaultInstanciaSection();
    return `instancia-section:${input.instanciaId}:${instanciaSection}`;
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

  if (
    activeNodeId.startsWith("section:") ||
    activeNodeId.startsWith("instancia:") ||
    activeNodeId.startsWith("instancia-section:")
  ) {
    expanded.add(`section:melhorias`);
  }

  if (activeNodeId.startsWith("revisao-section:") || activeNodeId.startsWith("revisao:")) {
    expanded.add(`section:melhorias`);
  }

  return expanded;
}
