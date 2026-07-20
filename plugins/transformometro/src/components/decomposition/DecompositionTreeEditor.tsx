import { useMemo } from "react";
import { Plus, Trash2 } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

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
import {
  canAcceptDecompositionDrop,
  moveDecompositionNode,
  type DropPosition,
} from "../../utils/decompositionReorder";
import { DecompositionRichTree } from "./DecompositionRichTree";
import { DS_GHOST_BTN } from "../ghostChrome";

type Props = {
  tree: DecompositionTreeV1;
  readOnly?: boolean;
  title?: string;
  invalidNodeIds?: ReadonlySet<string>;
  /** Quando false, oculta + Processo-chave (escopo parcial da melhoria). */
  allowRootProcessoChave?: boolean;
  onChange: (tree: DecompositionTreeV1) => void;
};

function isEditableNodeId(nodeId: string): boolean {
  return nodeId !== "decomposition-root";
}

export function DecompositionTreeEditor({
  tree,
  readOnly = false,
  title,
  invalidNodeIds,
  allowRootProcessoChave = true,
  onChange,
}: Props) {
  const nodeById = useMemo(() => new Map(tree.nodes.map((node) => [node.id, node])), [tree.nodes]);
  const richRoot = useMemo(
    () => buildDecompositionRichTree(tree, { title }),
    [tree, title]
  );
  const draggableNodeIds = useMemo(
    () => new Set(tree.nodes.filter((node) => !node.disabled).map((node) => node.id)),
    [tree.nodes]
  );
  const dragDrop = useMemo(
    () => ({
      draggableNodeIds,
      canDrop: (draggedId: string, targetId: string, position: DropPosition) =>
        canAcceptDecompositionDrop(tree.nodes, draggedId, targetId, position),
      onMove: (draggedId: string, targetId: string, position: DropPosition) => {
        onChange({
          ...tree,
          nodes: moveDecompositionNode(tree.nodes, draggedId, targetId, position),
        });
      },
    }),
    [draggableNodeIds, onChange, tree]
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
          className={`${DS_GHOST_BTN} tm-rich-tree__delete-btn`}
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
          {allowRootProcessoChave ? (
            <button type="button" className={DS_GHOST_BTN} onClick={() => addNode("processo_chave", null)}>
              <Plus size={14} />
              Processo-chave
            </button>
          ) : null}
          <span className="ds-hint tm-decomposition-editor__drag-hint">
            Arraste pelo ícone ⋮⋮ para reordenar ou mover entre processos-chave.
          </span>
        </div>
      ) : null}

      {!richRoot ? (
        <p className="ds-hint">{TM_HELP_TOOLTIPS.decomposition.arvoreVazia}</p>
      ) : (
        <DecompositionRichTree
          root={richRoot}
          expandDepth={2}
          enableDragDrop={!readOnly}
          dragDrop={readOnly ? undefined : dragDrop}
          renderLabel={
            readOnly
              ? undefined
              : (node) => {
                  const source = nodeById.get(node.id);
                  if (!source) {
                    return <span className="tm-rich-tree__label">{node.label}</span>;
                  }
                  const invalid = invalidNodeIds?.has(node.id) ?? false;
                  return (
                    <NativeTextControl
                      className={[
                        "tm-rich-tree__input",
                        invalid ? "tm-rich-tree__input--invalid" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      value={source.label ?? ""}
                      placeholder={DECOMPOSITION_LEVEL_LABELS[source.level]}
                      data-decomposition-node-id={node.id}
                      aria-invalid={invalid || undefined}
                      onChange={(label) => updateNode(node.id, { label })}
                      aria-label={`Rótulo ${source.label || DECOMPOSITION_LEVEL_LABELS[source.level]}`}
                    />
                  );
                }
          }
          renderActions={readOnly ? undefined : (node) => renderRowActions(node.id)}
          footerLabel={(count) => `${count} nó(s) no mapeamento`}
        />
      )}
    </div>
  );
}
