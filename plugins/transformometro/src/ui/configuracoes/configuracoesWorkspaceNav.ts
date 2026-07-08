import { CATALOG_CREATE } from "../../constants/catalogRoutes";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import type { Filial, RecursoCompartilhado, Setor } from "../../data/api/transformometroApi";
import {
  buildFilialPath,
  buildRecursoPath,
  buildRecursoSectionPath,
  buildSetorPath,
} from "../../utils/routeParser";

export type ConfiguracoesSectionId = "unidades" | "departamentos" | "recursos";

export type RecursoWorkspaceSectionId = "identificacao" | "custos" | "vinculos";

export type ConfiguracoesNavNodeKind = "section" | "filial" | "setor" | "recurso" | "recurso-section";

export type ConfiguracoesNavNode = {
  id: string;
  kind: ConfiguracoesNavNodeKind;
  label: string;
  searchText: string;
  href: string;
  depth: number;
  badge?: string;
  children?: ConfiguracoesNavNode[];
};

export const CONFIGURACOES_SECTIONS: Array<{ id: ConfiguracoesSectionId; label: string }> = [
  { id: "unidades", label: "Unidades" },
  { id: "departamentos", label: "Departamentos" },
  { id: "recursos", label: "Recursos compartilhados" },
];

export const RECURSO_WORKSPACE_SECTIONS: Array<{ id: RecursoWorkspaceSectionId; label: string }> = [
  { id: "identificacao", label: "Dados do recurso" },
  { id: "custos", label: "Custos ao longo do tempo" },
  { id: "vinculos", label: "Processos vinculados" },
];

const SECTION_IDS = new Set<string>(CONFIGURACOES_SECTIONS.map((item) => item.id));
const RECURSO_SECTION_IDS = new Set<string>(RECURSO_WORKSPACE_SECTIONS.map((item) => item.id));

export function isConfiguracoesSectionId(value: string): value is ConfiguracoesSectionId {
  return SECTION_IDS.has(value);
}

export function isRecursoWorkspaceSectionId(value: string): value is RecursoWorkspaceSectionId {
  return RECURSO_SECTION_IDS.has(value);
}

export function defaultConfiguracoesSection(): ConfiguracoesSectionId {
  return "unidades";
}

export function defaultRecursoSection(): RecursoWorkspaceSectionId {
  return "identificacao";
}

export function buildConfiguracoesSectionPath(section: ConfiguracoesSectionId): string {
  if (section === "unidades") return TRANSFORMOMETRO_ROUTES.configuracoesUnidades;
  if (section === "departamentos") return TRANSFORMOMETRO_ROUTES.configuracoesDepartamentos;
  return TRANSFORMOMETRO_ROUTES.configuracoesRecursos;
}

function isConfiguracoesWorkspacePath(path: string): boolean {
  return (
    path.includes("/configuracoes") ||
    path.includes("/cadastros") ||
    path.endsWith("/filiais") ||
    path.endsWith("/setores") ||
    (path.endsWith("/recursos") && !path.includes("/processos"))
  );
}

export function parseConfiguracoesSectionFromPath(pathname: string): ConfiguracoesSectionId {
  const path = pathname.replace(/\/$/, "");
  if (
    path.includes("/configuracoes/departamentos") ||
    path.includes("/cadastros/departamentos") ||
    path.endsWith("/setores")
  ) {
    return "departamentos";
  }
  if (
    path.includes("/configuracoes/recursos") ||
    path.includes("/cadastros/recursos") ||
    (path.endsWith("/recursos") && !path.includes("/processos"))
  ) {
    return "recursos";
  }
  if (
    path.includes("/configuracoes/unidades") ||
    path.includes("/cadastros/unidades") ||
    path.endsWith("/filiais")
  ) {
    return "unidades";
  }
  if (isConfiguracoesWorkspacePath(path)) return defaultConfiguracoesSection();
  return defaultConfiguracoesSection();
}

export function parseRecursoSectionFromHash(hash: string): RecursoWorkspaceSectionId {
  const raw = (hash.startsWith("#") ? hash.slice(1) : hash).trim().toLowerCase();
  if (raw && isRecursoWorkspaceSectionId(raw)) return raw;
  return defaultRecursoSection();
}

function filialLabel(filial: Filial): string {
  const code = filial.codigo_filial?.trim() || filial.filial_id.slice(0, 8);
  const name = filial.nome_filial?.trim() || "Unidade";
  return `${code} · ${name}`;
}

function setorLabel(setor: Setor): string {
  const code = setor.codigo_setor?.trim() || setor.setor_id.slice(0, 8);
  const name = setor.nome_setor?.trim() || "Departamento";
  return `${code} · ${name}`;
}

function recursoLabel(recurso: RecursoCompartilhado): string {
  const code = recurso.codigo_recurso?.trim() || recurso.recurso_compartilhado_id.slice(0, 8);
  const name = recurso.nome_recurso?.trim() || "Recurso";
  return `${code} · ${name}`;
}

function buildRecursoSectionNodes(recursoId: string): ConfiguracoesNavNode[] {
  return RECURSO_WORKSPACE_SECTIONS.map((section) => ({
    id: `recurso-section:${recursoId}:${section.id}`,
    kind: "recurso-section" as const,
    label: section.label,
    searchText: section.label.toLowerCase(),
    href: buildRecursoSectionPath(recursoId, section.id),
    depth: 3,
  }));
}

export function buildConfiguracoesWorkspaceTree(input: {
  filiais: Filial[];
  setores: Setor[];
  recursos: RecursoCompartilhado[];
}): ConfiguracoesNavNode[] {
  const { filiais, setores, recursos } = input;

  return CONFIGURACOES_SECTIONS.map((section) => {
    if (section.id === "unidades") {
      const children: ConfiguracoesNavNode[] = filiais.map((filial) => ({
        id: `filial:${filial.filial_id}`,
        kind: "filial",
        label: filialLabel(filial),
        searchText: filialLabel(filial).toLowerCase(),
        href: buildFilialPath(filial.filial_id),
        depth: 2,
      }));
      return {
        id: `section:unidades`,
        kind: "section" as const,
        label: section.label,
        searchText: section.label.toLowerCase(),
        href: buildConfiguracoesSectionPath("unidades"),
        depth: 1,
        badge: filiais.length ? String(filiais.length) : undefined,
        children,
      };
    }

    if (section.id === "departamentos") {
      const children: ConfiguracoesNavNode[] = setores.map((setor) => ({
        id: `setor:${setor.setor_id}`,
        kind: "setor",
        label: setorLabel(setor),
        searchText: setorLabel(setor).toLowerCase(),
        href: buildSetorPath(setor.setor_id),
        depth: 2,
      }));
      return {
        id: `section:departamentos`,
        kind: "section" as const,
        label: section.label,
        searchText: section.label.toLowerCase(),
        href: buildConfiguracoesSectionPath("departamentos"),
        depth: 1,
        badge: setores.length ? String(setores.length) : undefined,
        children,
      };
    }

    const children: ConfiguracoesNavNode[] = recursos.map((recurso) => {
      const label = recursoLabel(recurso);
      return {
        id: `recurso:${recurso.recurso_compartilhado_id}`,
        kind: "recurso" as const,
        label,
        searchText: label.toLowerCase(),
        href: buildRecursoPath(recurso.recurso_compartilhado_id),
        depth: 2,
        children: buildRecursoSectionNodes(recurso.recurso_compartilhado_id),
      };
    });

    return {
      id: `section:recursos`,
      kind: "section" as const,
      label: section.label,
      searchText: section.label.toLowerCase(),
      href: buildConfiguracoesSectionPath("recursos"),
      depth: 1,
      badge: recursos.length ? String(recursos.length) : undefined,
      children,
    };
  });
}

export function filterConfiguracoesTree(
  nodes: ConfiguracoesNavNode[],
  query: string
): ConfiguracoesNavNode[] {
  const q = query.trim().toLowerCase();
  if (!q) return nodes;

  function filterNode(node: ConfiguracoesNavNode): ConfiguracoesNavNode | null {
    const childMatches = (node.children ?? [])
      .map(filterNode)
      .filter((item): item is ConfiguracoesNavNode => item != null);
    const selfMatch = node.searchText.includes(q) || node.label.toLowerCase().includes(q);
    if (selfMatch) return { ...node, children: node.children };
    if (childMatches.length) return { ...node, children: childMatches };
    return null;
  }

  return nodes.map(filterNode).filter((item): item is ConfiguracoesNavNode => item != null);
}

export function collectConfiguracoesExpandedNodeIds(
  nodes: ConfiguracoesNavNode[],
  activeNodeId: string
): Set<string> {
  const expanded = new Set<string>();

  function walk(nodeList: ConfiguracoesNavNode[]): boolean {
    for (const node of nodeList) {
      if (node.id === activeNodeId) {
        return true;
      }
      if (node.children?.length && walk(node.children)) {
        expanded.add(node.id);
        return true;
      }
    }
    return false;
  }

  walk(nodes);

  if (activeNodeId.startsWith("filial:")) expanded.add("section:unidades");
  if (activeNodeId.startsWith("setor:")) expanded.add("section:departamentos");
  if (activeNodeId.startsWith("recurso:") || activeNodeId.startsWith("recurso-section:")) {
    expanded.add("section:recursos");
    const recursoId = activeNodeId.startsWith("recurso-section:")
      ? activeNodeId.split(":")[1]
      : activeNodeId.slice("recurso:".length);
    if (recursoId) expanded.add(`recurso:${recursoId}`);
  }

  return expanded;
}

export function resolveActiveConfiguracoesNodeId(input: {
  view: "configuracoes" | "filial" | "setor" | "recurso";
  section?: ConfiguracoesSectionId;
  filialId?: string;
  setorId?: string;
  recursoId?: string;
  recursoSection?: RecursoWorkspaceSectionId;
}): string {
  if (input.view === "filial" && input.filialId) {
    if (input.filialId === CATALOG_CREATE.filial) return "section:unidades";
    return `filial:${input.filialId}`;
  }
  if (input.view === "setor" && input.setorId) {
    if (input.setorId === CATALOG_CREATE.setor) return "section:departamentos";
    return `setor:${input.setorId}`;
  }
  if (input.view === "recurso" && input.recursoId) {
    if (input.recursoId === CATALOG_CREATE.recurso) return "section:recursos";
    if (input.recursoSection && input.recursoSection !== defaultRecursoSection()) {
      return `recurso-section:${input.recursoId}:${input.recursoSection}`;
    }
    return `recurso:${input.recursoId}`;
  }
  return `section:${input.section ?? defaultConfiguracoesSection()}`;
}
