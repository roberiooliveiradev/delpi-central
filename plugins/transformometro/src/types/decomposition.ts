export type DecompositionLevel = "processo_chave" | "tarefa" | "sub_tarefa";

export type DecompositionNode = {
  id: string;
  level: DecompositionLevel;
  ordem: number;
  label: string;
  parent_id?: string | null;
  descricao?: string | null;
  disabled?: boolean;
  highlight?: "asis" | "tobe" | "changed" | "removed";
  meta?: Record<string, unknown>;
};

export type DecompositionTreeV1 = {
  format: "decomposition_tree_v1";
  format_version: 1;
  nodes: DecompositionNode[];
};

export type DecompositionEscopo = {
  node_ids: string[];
  inherit_all: boolean;
  include_descendants: boolean;
};

export type DecompositionOverlayV1 = {
  format: "decomposition_overlay_v1";
  format_version: 1;
  node_overrides?: Record<
    string,
    {
      label?: string;
      descricao?: string | null;
      highlight?: "asis" | "tobe" | "changed" | "removed";
      meta?: Record<string, unknown>;
    }
  >;
  disabled_node_ids?: string[];
};

export type InstanciaContextoV1 = {
  format: "instancia_contexto_v1";
  format_version: 1;
  observacoes_rollout?: string | null;
  responsavel_local?: string | null;
  contato?: string | null;
  node_notes?: Record<
    string,
    {
      observacao?: string;
      responsavel?: string;
      sistema_local?: string;
    }
  >;
  links?: Array<{ titulo: string; url: string }>;
  meta?: Record<string, unknown>;
};

export type ProcessoDecompositionResponse = {
  processo_id: string | null;
  conteudo: DecompositionTreeV1;
  empty?: boolean;
  updated_at?: string;
};

export type DecompositionFlatRow = {
  departamento: string;
  macroprocesso: string;
  num_processo_chave: string;
  processo_chave: string;
  num_sub_tarefa: string;
  sub_tarefas: string;
  node_id: string;
  highlight: string;
};

export type MergedRevisaoDecomposition = {
  revisao_id: string;
  cenario_tipo?: string;
  tree: DecompositionTreeV1;
  escopo: DecompositionEscopo;
  overlay: DecompositionOverlayV1;
  warnings: string[];
  baseline_diff?: {
    changed: string[];
    added: string[];
    removed: string[];
  } | null;
};

export type ComposedProcessoDecomposition = {
  processo_id: string;
  at: string;
  instancia_id?: string | null;
  tree: DecompositionTreeV1;
  applied_revisoes: Array<{
    revisao_id: string;
    instancia_id: string;
    versao_revisao?: string;
    cenario_tipo?: string;
    data_inicio_vigencia?: string;
    node_ids_tocados: string[];
  }>;
  conflicts: Array<{
    node_id: string;
    field: string;
    winner_revisao_id: string;
    revisoes: Array<{
      revisao_id: string;
      versao_revisao?: string;
      label?: string | null;
      disabled?: boolean;
    }>;
  }>;
  base_node_count?: number;
};

export function emptyDecompositionTree(): DecompositionTreeV1 {
  return { format: "decomposition_tree_v1", format_version: 1, nodes: [] };
}

export function emptyDecompositionEscopo(): DecompositionEscopo {
  return { node_ids: [], inherit_all: true, include_descendants: true };
}

export function emptyDecompositionOverlay(): DecompositionOverlayV1 {
  return {
    format: "decomposition_overlay_v1",
    format_version: 1,
    node_overrides: {},
    disabled_node_ids: [],
  };
}

export function emptyInstanciaContexto(): InstanciaContextoV1 {
  return {
    format: "instancia_contexto_v1",
    format_version: 1,
    observacoes_rollout: null,
    responsavel_local: null,
    contato: null,
    node_notes: {},
    links: [],
    meta: {},
  };
}

export function createDecompositionNodeId(prefix = "n"): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 9)}`;
}

export const DECOMPOSITION_LEVEL_LABELS: Record<DecompositionLevel, string> = {
  processo_chave: "Processo-chave",
  tarefa: "Tarefa",
  sub_tarefa: "Sub-tarefa",
};

export function sortDecompositionNodes(nodes: DecompositionNode[]): DecompositionNode[] {
  const byParent = new Map<string | null, DecompositionNode[]>();
  for (const node of nodes) {
    const key = node.parent_id ?? null;
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key)!.push(node);
  }
  for (const group of byParent.values()) {
    group.sort((a, b) => a.ordem - b.ordem);
  }
  const result: DecompositionNode[] = [];
  function walk(parentId: string | null) {
    for (const node of byParent.get(parentId) ?? []) {
      if (node.disabled) continue;
      result.push(node);
      walk(node.id);
    }
  }
  walk(null);
  return result;
}

export function nextSiblingOrdem(nodes: DecompositionNode[], parentId: string | null): number {
  const siblings = nodes.filter((n) => (n.parent_id ?? null) === parentId && !n.disabled);
  if (!siblings.length) return 1;
  return Math.max(...siblings.map((n) => n.ordem)) + 1;
}
