import { useMemo } from "react";
import { Plus, Trash2 } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  DECOMPOSITION_LEVEL_LABELS,
  createDecompositionNodeId,
  nextSiblingOrdem,
  type DecompositionLevel,
  type DecompositionNode,
  type DecompositionTreeV1,
} from "../../types/decomposition";
import { buildDecompositionRichTree } from "../../utils/decompositionRichTree";
import { DecompositionRichTree } from "./DecompositionRichTree";

type Props = {
  tree: DecompositionTreeV1;
  readOnly?: boolean;
  title?: string;
  onChange: (tree: DecompositionTreeV1) => void;
};

function isEditableNodeId(nodeId: string): boolean {
  return nodeId !== "decomposition-root";
}

export function DecompositionTreeEditor({ tree, readOnly = false, title, onChange }: Props) {
  const nodeById = useMemo(() => new Map(tree.nodes.map((node) => [node.id, node])), [tree.nodes]);
  const richRoot = useMemo(
    () => buildDecompositionRichTree(tree, { title }),
    [tree, title]
  );

  function updateNodes(nextNodes: DecompositionNode[]) {
    onChange({ ...tree, nodes: nextNodes });
  }

  function addNode(level: DecompositionLevel, parentId: string | null) {
    const id = createDecompositionNodeId(
      level === "processo_chave" ? "pk" : level === "tarefa" ? "ta" : "st"
    );
    const node: DecompositionNode = {
      id,
      level,
      ordem: nextSiblingOrdem(tree.nodes, parentId),
      label: DECOMPOSITION_LEVEL_LABELS[level],
      parent_id: parentId,
      descricao: null,
    };
    updateNodes([...tree.nodes, node]);
  }

  function updateNode(nodeId: string, patch: Partial<DecompositionNode>) {
    updateNodes(tree.nodes.map((node) => (node.id === nodeId ? { ...node, ...patch } : node)));
  }

  function removeNode(nodeId: string) {
    const toRemove = new Set<string>([nodeId]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const node of tree.nodes) {
        if (node.parent_id && toRemove.has(node.parent_id) && !toRemove.has(node.id)) {
          toRemove.add(node.id);
          changed = true;
        }
      }
    }
    updateNodes(tree.nodes.filter((node) => !toRemove.has(node.id)));
  }

  function renderRowActions(nodeId: string) {
    if (!isEditableNodeId(nodeId)) return null;
    const source = nodeById.get(nodeId);
    if (!source) return null;

    return (
      <>
        {source.level === "processo_chave" ? (
          <>
            <button type="button" className="ds-link-btn" onClick={() => addNode("tarefa", nodeId)}>
              + Tarefa
            </button>
            <button type="button" className="ds-link-btn" onClick={() => addNode("sub_tarefa", nodeId)}>
              + Sub-tarefa
            </button>
          </>
        ) : null}
        {source.level === "tarefa" ? (
          <button type="button" className="ds-link-btn" onClick={() => addNode("sub_tarefa", nodeId)}>
            + Sub-tarefa
          </button>
        ) : null}
        <button
          type="button"
          className="ds-ghost-btn tm-rich-tree__delete-btn"
          aria-label="Excluir nó"
          onClick={() => removeNode(nodeId)}
        >
          <Trash2 size={14} />
        </button>
      </>
    );
  }

  return (
    <div className="tm-decomposition-editor">
      {!readOnly ? (
        <div className="tm-decomposition-editor__toolbar">
          <button type="button" className="ds-ghost-btn" onClick={() => addNode("processo_chave", null)}>
            <Plus size={14} />
            Processo-chave
          </button>
        </div>
      ) : null}

      {!richRoot ? (
        <p className="ds-hint">{TM_HELP_TOOLTIPS.decomposition.arvoreVazia}</p>
      ) : (
        <DecompositionRichTree
          root={richRoot}
          expandDepth={2}
          maxHeight={readOnly ? "480px" : "520px"}
          renderLabel={
            readOnly
              ? undefined
              : (node) =>
                  isEditableNodeId(node.id) ? (
                    <input
                      className="tm-rich-tree__input"
                      value={node.label}
                      onChange={(event) => updateNode(node.id, { label: event.target.value })}
                      aria-label={`Rótulo ${node.label}`}
                    />
                  ) : (
                    <span className="tm-rich-tree__label">{node.label}</span>
                  )
          }
          renderActions={readOnly ? undefined : (node) => renderRowActions(node.id)}
          footerLabel={(count) => `${count} nó(s) no mapeamento`}
        />
      )}
    </div>
  );
}
