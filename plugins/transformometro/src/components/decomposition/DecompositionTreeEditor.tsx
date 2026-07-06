import { Plus, Trash2 } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  DECOMPOSITION_LEVEL_LABELS,
  createDecompositionNodeId,
  nextSiblingOrdem,
  sortDecompositionNodes,
  type DecompositionLevel,
  type DecompositionNode,
  type DecompositionTreeV1,
} from "../../types/decomposition";

type Props = {
  tree: DecompositionTreeV1;
  readOnly?: boolean;
  onChange: (tree: DecompositionTreeV1) => void;
};

function depthForNode(node: DecompositionNode): number {
  if (node.level === "processo_chave") return 0;
  if (node.level === "tarefa") return 1;
  return 2;
}

export function DecompositionTreeEditor({ tree, readOnly = false, onChange }: Props) {
  const visibleNodes = sortDecompositionNodes(tree.nodes);

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
    updateNodes(
      tree.nodes.map((node) => (node.id === nodeId ? { ...node, ...patch } : node))
    );
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

      {visibleNodes.length === 0 ? (
        <p className="ds-hint">{TM_HELP_TOOLTIPS.decomposition.arvoreVazia}</p>
      ) : (
        <ul className="tm-decomposition-tree">
          {visibleNodes.map((node) => (
            <li
              key={node.id}
              className="tm-decomposition-tree__item"
              style={{ paddingLeft: `${depthForNode(node) * 1.25}rem` }}
            >
              <span className="tm-decomposition-tree__badge">{DECOMPOSITION_LEVEL_LABELS[node.level]}</span>
              {readOnly ? (
                <span className="tm-decomposition-tree__label">{node.label}</span>
              ) : (
                <input
                  className="tm-decomposition-tree__input"
                  value={node.label}
                  onChange={(event) => updateNode(node.id, { label: event.target.value })}
                  aria-label={`Rótulo ${node.id}`}
                />
              )}
              {!readOnly ? (
                <span className="tm-decomposition-tree__actions">
                  {node.level === "processo_chave" ? (
                    <>
                      <button
                        type="button"
                        className="ds-link-btn"
                        onClick={() => addNode("tarefa", node.id)}
                      >
                        + Tarefa
                      </button>
                      <button
                        type="button"
                        className="ds-link-btn"
                        onClick={() => addNode("sub_tarefa", node.id)}
                      >
                        + Sub-tarefa
                      </button>
                    </>
                  ) : null}
                  {node.level === "tarefa" ? (
                    <button
                      type="button"
                      className="ds-link-btn"
                      onClick={() => addNode("sub_tarefa", node.id)}
                    >
                      + Sub-tarefa
                    </button>
                  ) : null}
                  <button
                    type="button"
                    className="ds-ghost-btn"
                    aria-label="Excluir nó"
                    onClick={() => removeNode(node.id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
