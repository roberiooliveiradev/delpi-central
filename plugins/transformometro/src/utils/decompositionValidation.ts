import {
  DECOMPOSITION_LEVEL_LABELS,
  type DecompositionLevel,
  type DecompositionNode,
  type DecompositionTreeV1,
} from "../types/decomposition";

export type DecompositionValidationIssue = {
  nodeId?: string;
  field: string;
  message: string;
  path: string;
};

export type DecompositionValidationReport = {
  valid: boolean;
  issues: DecompositionValidationIssue[];
};

const LEVEL_ARTICLE: Record<DecompositionLevel, string> = {
  processo_chave: "do",
  tarefa: "da",
  sub_tarefa: "da",
};

function nodeDisplayLabel(node: DecompositionNode): string {
  const trimmed = node.label?.trim();
  if (trimmed) return trimmed;
  return `${DECOMPOSITION_LEVEL_LABELS[node.level]} (ordem ${node.ordem})`;
}

export function decompositionNodePath(nodes: DecompositionNode[], nodeId: string): string {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const parts: string[] = [];
  let current: string | null = nodeId;

  while (current) {
    const node = byId.get(current);
    if (!node) break;
    parts.unshift(nodeDisplayLabel(node));
    current = node.parent_id ?? null;
  }

  return parts.join(" → ");
}

function emptyLabelIssue(node: DecompositionNode, nodes: DecompositionNode[]): DecompositionValidationIssue {
  const levelLabel = DECOMPOSITION_LEVEL_LABELS[node.level].toLowerCase();
  const path = decompositionNodePath(nodes, node.id);
  return {
    nodeId: node.id,
    field: "label",
    path,
    message: `Informe o nome ${LEVEL_ARTICLE[node.level]} ${levelLabel} «${path}».`,
  };
}

export function validateDecompositionTreeForSave(tree: DecompositionTreeV1): DecompositionValidationReport {
  const activeNodes = tree.nodes.filter((node) => !node.disabled);
  const issues: DecompositionValidationIssue[] = [];

  for (const node of activeNodes) {
    if (!node.label?.trim()) {
      issues.push(emptyLabelIssue(node, activeNodes));
    }
  }

  return { valid: issues.length === 0, issues };
}

const API_ERROR_PATTERNS: Array<{ pattern: RegExp; message: string }> = [
  {
    pattern: /^nodes\[\d+\]\.label obrigatório\.$/,
    message: "Há um item sem nome na árvore. Preencha todos os rótulos antes de salvar.",
  },
  {
    pattern: /^Máximo de \d+ nós\.$/,
    message: "O mapeamento excede o limite de nós permitido. Reduza a árvore antes de salvar.",
  },
  {
    pattern: /^Máximo de \d+ processos-chave\.$/,
    message: "O mapeamento excede o limite de processos-chave. Reduza a árvore antes de salvar.",
  },
  {
    pattern: /^node_id duplicado:/,
    message: "Há IDs duplicados na árvore. Recarregue a página e tente novamente.",
  },
  {
    pattern: /^ordem duplicada entre irmãos/,
    message: "Há itens com a mesma ordem no mesmo nível. Recarregue a página e tente novamente.",
  },
];

export function humanizeDecompositionApiError(
  message: string,
  tree?: DecompositionTreeV1 | null
): DecompositionValidationReport {
  const labelMatch = message.match(/^nodes\[(\d+)\]\.label obrigatório\.$/);
  if (labelMatch && tree) {
    const index = Number(labelMatch[1]);
    const node = tree.nodes[index];
    if (node) {
      const activeNodes = tree.nodes.filter((item) => !item.disabled);
      return {
        valid: false,
        issues: [emptyLabelIssue(node, activeNodes)],
      };
    }
  }

  if (tree) {
    const clientReport = validateDecompositionTreeForSave(tree);
    if (!clientReport.valid) {
      return clientReport;
    }
  }

  const mapped = API_ERROR_PATTERNS.find(({ pattern }) => pattern.test(message));
  return {
    valid: false,
    issues: [
      {
        field: "general",
        path: "",
        message: mapped?.message ?? message,
      },
    ],
  };
}

export function scrollToDecompositionNode(nodeId: string): void {
  document
    .querySelector<HTMLElement>(`[data-decomposition-node-id="${nodeId}"]`)
    ?.scrollIntoView({ block: "nearest", behavior: "smooth" });
}
