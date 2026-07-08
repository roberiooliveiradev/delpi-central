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

export type ProcessoWorkspaceNodeKind = "section" | "instancia" | "revisao";

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

const SECTION_IDS = new Set<string>(PROCESSO_WORKSPACE_SECTIONS.map((item) => item.id));

export function isProcessoWorkspaceSectionId(value: string): value is ProcessoWorkspaceSectionId {
  return SECTION_IDS.has(value);
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
        return {
          id: `revisao:${revisao.revisao_id}`,
          kind: "revisao" as const,
          label: revLabel,
          searchText: `${revLabel} ${revisao.versao_revisao ?? ""} ${revisao.cenario_tipo ?? ""}`.toLowerCase(),
          href: buildProcessoPath(processoId, revisao.revisao_id, instancia.instancia_id),
          depth: 3,
          matrixBadge,
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
}): string {
  if (input.view === "revisao" && input.revisaoId) {
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

  return expanded;
}
