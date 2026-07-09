import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type DragEvent,
  type ReactNode,
} from "react";
import { GripVertical } from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { RichTreeNode } from "../../types/richTree";
import { countRichTreeNodes } from "../../utils/decompositionRichTree";
import {
  resolveDecompositionDropPosition,
  type DropPosition,
} from "../../utils/decompositionReorder";

const BADGE_CLASS_BY_CODE: Record<string, string> = {
  PK: "tm-rich-tree__badge--pk",
  T: "tm-rich-tree__badge--t",
  ST: "tm-rich-tree__badge--st",
};

const BADGE_HINTS: Record<string, string> = {
  PK: "Processo-chave — bloco principal do WBS.",
  T: "Tarefa — etapa dentro do processo-chave.",
  ST: "Sub-tarefa — detalhamento da tarefa ou do processo-chave.",
};

const HIGHLIGHT_CLASS: Record<NonNullable<RichTreeNode["highlight"]>, string> = {
  asis: "tm-rich-tree__row--asis",
  tobe: "tm-rich-tree__row--tobe",
  changed: "tm-rich-tree__row--changed",
  removed: "tm-rich-tree__row--removed",
};

type DropTarget = {
  nodeId: string;
  position: DropPosition;
};

type DragDropContextValue = {
  dragNodeId: string | null;
  dropTarget: DropTarget | null;
  startDrag: (nodeId: string, event: DragEvent<HTMLElement>) => void;
  endDrag: () => void;
  updateDropTarget: (nodeId: string, event: DragEvent<HTMLElement>) => void;
  clearDropTarget: () => void;
  commitDrop: (event: DragEvent<HTMLElement>) => void;
  isDraggable: (nodeId: string) => boolean;
  getDropClass: (nodeId: string) => string;
};

const DragDropContext = createContext<DragDropContextValue | null>(null);

function TreeChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className="tm-rich-tree__toggle-icon"
      width="12"
      height="12"
      viewBox="0 0 12 12"
      aria-hidden="true"
      focusable="false"
    >
      {expanded ? (
        <path
          d="M2.5 4.5 6 8 9.5 4.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          d="M4.5 2.5 8 6 4.5 9.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

type RowSlots = {
  renderLabel?: (node: RichTreeNode) => ReactNode;
  renderActions?: (node: RichTreeNode) => ReactNode;
};

type RichTreeNodeRowProps = RowSlots & {
  node: RichTreeNode;
  depth: number;
  defaultExpanded: boolean;
  expandDepth: number;
  enableDragDrop?: boolean;
};

function RichTreeNodeRow({
  node,
  depth,
  defaultExpanded,
  expandDepth,
  renderLabel,
  renderActions,
  enableDragDrop = false,
}: RichTreeNodeRowProps) {
  const dragDrop = useContext(DragDropContext);
  const hasChildren = Boolean(node.children?.length);
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0);
  const badgeCode = String(node.badge ?? "").trim().toUpperCase();
  const badgeClass = BADGE_CLASS_BY_CODE[badgeCode] ?? "";
  const badgeHint = BADGE_HINTS[badgeCode] ?? TM_HELP_TOOLTIPS.decomposition.mapeamento;
  const highlightClass = node.highlight ? HIGHLIGHT_CLASS[node.highlight] : "";
  const draggable = enableDragDrop && (dragDrop?.isDraggable(node.id) ?? false);
  const dropClass = enableDragDrop ? (dragDrop?.getDropClass(node.id) ?? "") : "";
  const isDragging = dragDrop?.dragNodeId === node.id;

  return (
    <li className="tm-rich-tree__item">
      <div
        className={[
          "tm-rich-tree__row",
          highlightClass,
          dropClass,
          isDragging ? "tm-rich-tree__row--dragging" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        style={{ paddingLeft: `${depth * 1.1 + 0.35}rem` }}
        onDragOver={
          enableDragDrop
            ? (event) => {
                event.preventDefault();
                dragDrop?.updateDropTarget(node.id, event);
              }
            : undefined
        }
        onDrop={
          enableDragDrop
            ? (event) => {
                event.preventDefault();
                dragDrop?.commitDrop(event);
              }
            : undefined
        }
      >
        {draggable ? (
          <button
            type="button"
            className="tm-rich-tree__drag-handle"
            draggable
            aria-label="Arrastar para reordenar"
            title="Arrastar para reordenar ou mover entre seções"
            onDragStart={(event) => dragDrop?.startDrag(node.id, event)}
            onDragEnd={() => dragDrop?.endDrag()}
          >
            <GripVertical size={14} aria-hidden="true" />
          </button>
        ) : (
          <span className="tm-rich-tree__drag-spacer" aria-hidden="true" />
        )}

        {hasChildren ? (
          <button
            type="button"
            className={`tm-rich-tree__toggle ${
              expanded ? "tm-rich-tree__toggle--expanded" : "tm-rich-tree__toggle--collapsed"
            }`}
            aria-label={expanded ? "Recolher ramo" : "Expandir ramo"}
            aria-expanded={expanded}
            onClick={(event) => {
              event.stopPropagation();
              setExpanded((value) => !value);
            }}
          >
            <TreeChevronIcon expanded={expanded} />
          </button>
        ) : (
          <span className="tm-rich-tree__toggle-spacer" aria-hidden="true" />
        )}

        <div className="tm-rich-tree__content">
          <div className="tm-rich-tree__primary">
            {renderLabel ? (
              renderLabel(node)
            ) : (
              <span className="tm-rich-tree__label" title={node.label}>
                {node.label}
              </span>
            )}
            {node.badge ? (
              <span className={`tm-rich-tree__badge ${badgeClass}`.trim()} title={badgeHint}>
                {node.badge}
              </span>
            ) : null}
            {node.metaCaption ? <span className="tm-rich-tree__meta">{node.metaCaption}</span> : null}
            {renderActions ? (
              <span className="tm-rich-tree__row-actions">{renderActions(node)}</span>
            ) : null}
          </div>
          {node.subtitle ? <div className="tm-rich-tree__subtitle">{node.subtitle}</div> : null}
        </div>
      </div>

      {hasChildren && expanded ? (
        <ul className="tm-rich-tree__children">
          {node.children!.map((child) => (
            <RichTreeNodeRow
              key={child.id}
              node={child}
              depth={depth + 1}
              defaultExpanded={depth < expandDepth}
              expandDepth={expandDepth}
              renderLabel={renderLabel}
              renderActions={renderActions}
              enableDragDrop={enableDragDrop}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export type DecompositionDragDropConfig = {
  draggableNodeIds: ReadonlySet<string>;
  canDrop: (draggedId: string, targetId: string, position: DropPosition) => boolean;
  onMove: (draggedId: string, targetId: string, position: DropPosition) => void;
};

type DecompositionRichTreeProps = RowSlots & {
  root: RichTreeNode;
  expandDepth?: number;
  maxHeight?: string;
  footerLabel?: (nodeCount: number) => string;
  enableDragDrop?: boolean;
  dragDrop?: DecompositionDragDropConfig;
};

export function DecompositionRichTree({
  root,
  expandDepth = 2,
  maxHeight,
  footerLabel = (nodeCount) => `${nodeCount} nó(s) no mapeamento`,
  renderLabel,
  renderActions,
  enableDragDrop = false,
  dragDrop,
}: DecompositionRichTreeProps) {
  const nodeCount = useMemo(() => countRichTreeNodes(root), [root]);
  const [dragNodeId, setDragNodeId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<DropTarget | null>(null);

  const startDrag = useCallback((nodeId: string, event: DragEvent<HTMLElement>) => {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", nodeId);
    setDragNodeId(nodeId);
    setDropTarget(null);
  }, []);

  const endDrag = useCallback(() => {
    setDragNodeId(null);
    setDropTarget(null);
  }, []);

  const updateDropTarget = useCallback(
    (nodeId: string, event: DragEvent<HTMLElement>) => {
      if (!dragNodeId || !dragDrop) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const canDropInside = dragDrop.canDrop(dragNodeId, nodeId, "inside");
      const position = resolveDecompositionDropPosition(
        event.clientY - rect.top,
        rect.height,
        canDropInside
      );

      if (!dragDrop.canDrop(dragNodeId, nodeId, position)) {
        const fallbackPosition = position === "inside" ? "after" : position;
        if (!dragDrop.canDrop(dragNodeId, nodeId, fallbackPosition)) {
          setDropTarget(null);
          return;
        }
        setDropTarget({ nodeId, position: fallbackPosition });
        return;
      }

      setDropTarget({ nodeId, position });
    },
    [dragDrop, dragNodeId]
  );

  const clearDropTarget = useCallback(() => {
    setDropTarget(null);
  }, []);

  const commitDrop = useCallback(
    (event: DragEvent<HTMLElement>) => {
      if (!dragDrop) return;
      const draggedId = event.dataTransfer.getData("text/plain") || dragNodeId;
      if (!draggedId || !dropTarget) {
        endDrag();
        return;
      }
      if (dragDrop.canDrop(draggedId, dropTarget.nodeId, dropTarget.position)) {
        dragDrop.onMove(draggedId, dropTarget.nodeId, dropTarget.position);
      }
      endDrag();
    },
    [dragDrop, dragNodeId, dropTarget, endDrag]
  );

  const getDropClass = useCallback(
    (nodeId: string) => {
      if (!dropTarget || dropTarget.nodeId !== nodeId) return "";
      if (dropTarget.position === "inside") return "tm-rich-tree__row--drop-inside";
      if (dropTarget.position === "before") return "tm-rich-tree__row--drop-before";
      return "tm-rich-tree__row--drop-after";
    },
    [dropTarget]
  );

  const dragDropContext = useMemo<DragDropContextValue | null>(() => {
    if (!enableDragDrop || !dragDrop) return null;
    return {
      dragNodeId,
      dropTarget,
      startDrag,
      endDrag,
      updateDropTarget,
      clearDropTarget,
      commitDrop,
      isDraggable: (nodeId) => dragDrop.draggableNodeIds.has(nodeId),
      getDropClass,
    };
  }, [
    clearDropTarget,
    commitDrop,
    dragDrop,
    dragNodeId,
    dropTarget,
    enableDragDrop,
    endDrag,
    getDropClass,
    startDrag,
    updateDropTarget,
  ]);

  const treeBody = (
    <div
      className="tm-rich-tree__scroll"
      style={maxHeight ? { maxHeight } : undefined}
    >
      <ul className="tm-rich-tree__list">
        <RichTreeNodeRow
          node={root}
          depth={0}
          defaultExpanded
          expandDepth={expandDepth}
          renderLabel={renderLabel}
          renderActions={renderActions}
          enableDragDrop={enableDragDrop}
        />
      </ul>
    </div>
  );

  return (
    <div className={["tm-rich-tree", enableDragDrop ? "tm-rich-tree--draggable" : ""].filter(Boolean).join(" ")}>
      {dragDropContext ? (
        <DragDropContext.Provider value={dragDropContext}>{treeBody}</DragDropContext.Provider>
      ) : (
        treeBody
      )}
      <div className="tm-rich-tree__footer">{footerLabel(nodeCount)}</div>
    </div>
  );
}
