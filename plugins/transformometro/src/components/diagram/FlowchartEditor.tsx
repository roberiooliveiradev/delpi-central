import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  useOnSelectionChange,
  useReactFlow,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";

import { useTransformometroDarkMode } from "../../hooks/useTransformometroDarkMode";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";
import { useConfirm } from "../ui/ConfirmDialogProvider";
import { TabPanelTransition } from "../TabPanelTransition";
import {
  DIAGRAM_EDITOR_ACTIONS,
  DIAGRAM_EDITOR_SELECTION_ACTIONS,
} from "./flowchartEditorToolbar";
import {
  autoLayoutFlowchart,
  canvasHeightForLanes,
  defaultNodePosition,
  laneIndexFromDragY,
  laneTopOffset,
  normalizeLanes,
  removeLane,
  renameLane,
  reorderLanes,
  snapNodeToLane,
} from "../../utils/diagramSwimlanes";
import {
  FLOWCHART_NODE_PALETTE,
  applyDecisionTemplate,
  applyLinearTemplate,
  applySwimlaneBpmnTemplate,
  createEdgeId,
  createLaneId,
  createNodeId,
  type FlowchartNode,
  type FlowchartNodeType,
  type FlowchartV1,
} from "../../types/diagram";
import { FlowchartBpmnNode, type BpmnNodeData } from "./FlowchartBpmnNode";
import { FlowchartLaneNode } from "./FlowchartLaneNode";
import { FlowchartEditableEdge } from "./FlowchartEditableEdge";
import { FlowchartMermaidPanel } from "./FlowchartMermaidPanel";
import {
  FlowchartEditorToolbar,
  type FlowchartEditorToolbarTab,
} from "./FlowchartEditorToolbar";
import { FlowchartEditorActionDock } from "./FlowchartEditorActionDock";
import { useDiagramEditorLayout } from "./DiagramLayoutContext";
import {
  createStarterMermaidTemplate,
  flowchartToMermaid,
  mermaidToFlowchart,
  MermaidImportError,
} from "../../utils/flowchartMermaid";

type FlowchartEditorProps = {
  value: FlowchartV1;
  onChange?: (next: FlowchartV1) => void;
  readOnly?: boolean;
  scopeNodeIds?: Set<string> | null;
  selectedScopeIds?: Set<string>;
  onToggleScopeNode?: (nodeId: string) => void;
  diffNodeIds?: { changed?: string[]; added?: string[]; removed?: string[] };
  showTemplates?: boolean;
  showPreviewTab?: boolean;
  exportRef?: RefObject<HTMLDivElement | null>;
};

type ActivityNode = Node<BpmnNodeData>;
type LaneNode = Node<{
  label: string;
  height: number;
  laneId?: string;
  isActive?: boolean;
  readOnly?: boolean;
  onRename?: (laneId: string, label: string) => void;
  onSelect?: (laneId: string) => void;
}>;
type EditorNode = Node;

const nodeTypes = {
  flowchart: FlowchartBpmnNode,
  lane: FlowchartLaneNode,
};

const edgeTypes = {
  flowchart: FlowchartEditableEdge,
};

const LANE_NODE_PREFIX = "__lane__";
const DUPLICATE_OFFSET = 48;
const NUDGE_STEP = 8;
const DEFAULT_CANVAS_HEIGHT = 680;
const STAGE_MIN_HEIGHT = 680;

type SelectionClipboard = {
  nodes: ActivityNode[];
  edges: Edge[];
};

function isLaneNodeId(id: string): boolean {
  return id.startsWith(LANE_NODE_PREFIX);
}

function buildLaneNodes(
  lanes: ReturnType<typeof normalizeLanes>,
  options?: {
    readOnly?: boolean;
    activeLaneId?: string;
    onRenameLane?: (laneId: string, label: string) => void;
    onSelectLane?: (laneId: string) => void;
  }
): LaneNode[] {
  return lanes.map((lane) => ({
    id: `${LANE_NODE_PREFIX}${lane.id}`,
    type: "lane",
    position: { x: 0, y: laneTopOffset(lanes, lane.id) },
    data: {
      label: lane.label,
      height: lane.height ?? 168,
      laneId: lane.id,
      isActive: options?.activeLaneId === lane.id,
      readOnly: options?.readOnly ?? true,
      onRename: options?.onRenameLane,
      onSelect: options?.onSelectLane,
    },
    draggable: !(options?.readOnly ?? true),
    dragHandle: ".tm-diagram-lane__header--draggable",
    selectable: false,
    connectable: false,
    focusable: false,
    deletable: false,
    zIndex: -1,
  }));
}

function toReactFlow(
  value: FlowchartV1,
  laneOptions?: {
    readOnly?: boolean;
    activeLaneId?: string;
    onRenameLane?: (laneId: string, label: string) => void;
    onSelectLane?: (laneId: string) => void;
  }
): { nodes: EditorNode[]; edges: Edge[] } {
  const lanes = normalizeLanes(value.lanes);
  const activityNodes: ActivityNode[] = value.nodes.map((node) => ({
    id: node.id,
    type: "flowchart",
    position: node.position,
    data: {
      label: node.label,
      nodeType: node.type,
      highlight: node.highlight,
      manual: node.meta?.manual ?? node.type === "process",
    },
    zIndex: 1,
  }));

  const edges: Edge[] = value.edges.map((edge) => ({
    id: edge.id,
    source: edge.from,
    target: edge.to,
    type: "flowchart",
    label: edge.label ?? undefined,
    labelStyle: { fontSize: 11, fontWeight: 600 },
    labelBgStyle: { fillOpacity: 0.92 },
  }));

  return {
    nodes: [...buildLaneNodes(lanes, laneOptions), ...activityNodes],
    edges,
  };
}

function fromReactFlow(
  nodes: EditorNode[],
  edges: Edge[],
  base: FlowchartV1
): FlowchartV1 {
  const lanes = normalizeLanes(base.lanes);
  const activityNodes: FlowchartNode[] = nodes
    .filter((node) => node.type !== "lane")
    .map((node) => {
      const data = node.data as BpmnNodeData;
      return {
        id: node.id,
        type: data.nodeType,
        label: data.label,
        position: node.position,
        lane_id: lanes.length
          ? snapNodeToLane(
              {
                id: node.id,
                type: data.nodeType,
                label: data.label,
                position: node.position,
              },
              lanes
            ).lane_id
          : undefined,
        highlight: data.highlight as FlowchartNode["highlight"],
        meta: data.nodeType === "process" ? { manual: data.manual !== false } : undefined,
      };
    });

  return {
    ...base,
    lanes: lanes.length ? lanes : undefined,
    nodes: activityNodes,
    edges: edges
      .filter((edge) => !isLaneNodeId(edge.source) && !isLaneNodeId(edge.target))
      .map((edge) => ({
        id: edge.id,
        from: edge.source,
        to: edge.target,
        label: typeof edge.label === "string" ? edge.label : null,
        routing:
          edge.type === "step" || edge.type === "straight" || edge.type === "smoothstep"
            ? edge.type
            : "smoothstep",
      })),
  };
}

function FlowchartEditorInner({
  value,
  onChange,
  readOnly = false,
  scopeNodeIds,
  selectedScopeIds,
  onToggleScopeNode,
  diffNodeIds,
  showTemplates = true,
  showPreviewTab = true,
  exportRef,
}: FlowchartEditorProps) {
  const confirm = useConfirm();
  const lanes = useMemo(() => normalizeLanes(value.lanes), [value.lanes]);
  const [activeLaneId, setActiveLaneId] = useState<string | undefined>(lanes[0]?.id);

  const handleRenameLane = useCallback(
    (laneId: string, label: string) => {
      if (readOnly) return;
      onChange?.(renameLane(value, laneId, label));
    },
    [onChange, readOnly, value]
  );

  const handleSelectLane = useCallback((laneId: string) => {
    setActiveLaneId(laneId);
  }, []);

  const laneRenderOptions = useMemo(
    () => ({
      readOnly,
      activeLaneId,
      onRenameLane: readOnly ? undefined : handleRenameLane,
      onSelectLane: readOnly ? undefined : handleSelectLane,
    }),
    [activeLaneId, handleRenameLane, handleSelectLane, readOnly]
  );

  const initial = useMemo(() => toReactFlow(value, laneRenderOptions), [laneRenderOptions, value]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [activeTab, setActiveTab] = useState<"canvas" | "mermaid">("canvas");
  const [toolbarTab, setToolbarTab] = useState<FlowchartEditorToolbarTab>("elements");
  const [mermaidDraft, setMermaidDraft] = useState("");
  const [mermaidApplyError, setMermaidApplyError] = useState<string | null>(null);
  const [mermaidApplying, setMermaidApplying] = useState(false);
  const canvasMermaid = useMemo(() => flowchartToMermaid(value), [value]);
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
  const [selectedEdgeIds, setSelectedEdgeIds] = useState<string[]>([]);
  const clipboardRef = useRef<SelectionClipboard | null>(null);
  const canvasWrapperRef = useRef<HTMLDivElement>(null);
  const isDark = useTransformometroDarkMode();
  const colorMode = isDark ? "dark" : "light";
  const layout = useDiagramEditorLayout();
  const { fitView } = useReactFlow();
  const canvasHeight = Math.max(
    canvasHeightForLanes(lanes, lanes.length ? 380 : DEFAULT_CANVAS_HEIGHT),
    STAGE_MIN_HEIGHT
  );
  const hasNodeSelection = selectedNodeIds.length > 0;
  const hasSelection = hasNodeSelection || selectedEdgeIds.length > 0;

  useOnSelectionChange({
    onChange: ({ nodes: selectedNodes, edges: selectedEdges }) => {
      setSelectedNodeIds(
        selectedNodes.filter((node) => node.type !== "lane").map((node) => node.id)
      );
      setSelectedEdgeIds(selectedEdges.map((edge) => edge.id));
    },
  });

  useEffect(() => {
    if (lanes.length && !lanes.some((lane) => lane.id === activeLaneId)) {
      setActiveLaneId(lanes[0]?.id);
    }
  }, [activeLaneId, lanes]);

  const switchToMermaidTab = useCallback(() => {
    setMermaidDraft(canvasMermaid);
    setMermaidApplyError(null);
    setActiveTab("mermaid");
  }, [canvasMermaid]);

  const refreshMermaidFromCanvas = useCallback(() => {
    setMermaidDraft(canvasMermaid);
    setMermaidApplyError(null);
  }, [canvasMermaid]);

  const applyMermaidDraft = useCallback(() => {
    if (readOnly) return;
    setMermaidApplying(true);
    setMermaidApplyError(null);
    try {
      const parsed = mermaidToFlowchart(mermaidDraft, value);
      const laidOut = autoLayoutFlowchart(parsed);
      onChange?.(laidOut);
      setActiveTab("canvas");
    } catch (err) {
      setMermaidApplyError(
        err instanceof MermaidImportError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Não foi possível interpretar o código Mermaid."
      );
    } finally {
      setMermaidApplying(false);
    }
  }, [mermaidDraft, onChange, readOnly, value]);

  const useMermaidTemplate = useCallback(() => {
    setMermaidDraft(createStarterMermaidTemplate());
    setMermaidApplyError(null);
  }, []);

  useEffect(() => {
    if (activeTab !== "canvas") return;
    const element = canvasWrapperRef.current;
    if (!element) return;

    const syncViewport = () => {
      const { width, height } = element.getBoundingClientRect();
      if (width < 8 || height < 8) return;
      window.requestAnimationFrame(() => {
        void fitView({ padding: 0.15, duration: 0 });
      });
    };

    syncViewport();

    const resizeObserver = new ResizeObserver(syncViewport);
    resizeObserver.observe(element);

    const intersectionObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          syncViewport();
        }
      },
      { threshold: 0.01 }
    );
    intersectionObserver.observe(element);

    return () => {
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
    };
  }, [activeTab, fitView, nodes.length, edges.length]);

  const emitChange = useCallback(
    (nextNodes: EditorNode[], nextEdges: Edge[]) => {
      onChange?.(fromReactFlow(nextNodes, nextEdges, value));
    },
    [onChange, value]
  );

  const handleNodeLabelChange = useCallback(
    (nodeId: string, label: string) => {
      if (readOnly) return;
      setNodes((currentNodes) => {
        const nextNodes = currentNodes.map((item) =>
          item.id === nodeId && item.type !== "lane"
            ? {
                ...item,
                data: { ...(item.data as BpmnNodeData), label },
              }
            : item
        );
        setEdges((currentEdges) => {
          emitChange(nextNodes, currentEdges);
          return currentEdges;
        });
        return nextNodes;
      });
    },
    [emitChange, readOnly, setEdges, setNodes]
  );

  const handleEdgeLabelChange = useCallback(
    (edgeId: string, label: string) => {
      if (readOnly) return;
      setEdges((currentEdges) => {
        const nextEdges = currentEdges.map((item) =>
          item.id === edgeId ? { ...item, label: label || undefined } : item
        );
        setNodes((currentNodes) => {
          emitChange(currentNodes, nextEdges);
          return currentNodes;
        });
        return nextEdges;
      });
    },
    [emitChange, readOnly, setEdges, setNodes]
  );

  useEffect(() => {
    const next = toReactFlow(value, laneRenderOptions);
    setNodes(
      next.nodes.map((node) => {
        if (node.type === "lane") {
          return {
            ...node,
            draggable: !readOnly,
            dragHandle: ".tm-diagram-lane__header--draggable",
          };
        }
        return {
          ...node,
          draggable: !readOnly,
          selectable: !readOnly,
          data:
            node.type === "lane"
              ? node.data
              : {
                  ...(node.data as BpmnNodeData),
                  readOnly,
                  onLabelChange: readOnly ? undefined : handleNodeLabelChange,
                  scopeSelectable: Boolean(onToggleScopeNode) && !readOnly,
                  inScope: selectedScopeIds
                    ? selectedScopeIds.has(node.id)
                    : scopeNodeIds?.has(node.id),
                  onToggleScope: onToggleScopeNode,
                  highlight:
                    diffNodeIds?.added?.includes(node.id)
                      ? "tobe"
                      : diffNodeIds?.changed?.includes(node.id)
                        ? "changed"
                        : diffNodeIds?.removed?.includes(node.id)
                          ? "removed"
                          : (node.data as BpmnNodeData).highlight,
                },
        };
      })
    );
    setEdges(
      next.edges.map((edge) => ({
        ...edge,
        type: "flowchart",
        animated: false,
        data: {
          readOnly,
          onLabelChange: readOnly ? undefined : handleEdgeLabelChange,
        },
      }))
    );
  }, [
    value,
    readOnly,
    scopeNodeIds,
    selectedScopeIds,
    onToggleScopeNode,
    diffNodeIds,
    laneRenderOptions,
    handleNodeLabelChange,
    handleEdgeLabelChange,
    setNodes,
    setEdges,
  ]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly) return;
      setEdges((current) => {
        const next = addEdge(
          {
            ...connection,
            id: createEdgeId(),
            type: "flowchart",
            data: {
              readOnly,
              onLabelChange: handleEdgeLabelChange,
            },
            labelStyle: { fontSize: 11, fontWeight: 600 },
            labelBgStyle: { fillOpacity: 0.92 },
          },
          current
        );
        emitChange(nodes, next);
        return next;
      });
    },
    [emitChange, handleEdgeLabelChange, nodes, readOnly, setEdges]
  );

  const onNodeDrag = useCallback(
    (_: unknown, node: EditorNode) => {
      if (readOnly || node.type !== "lane") return;
      if (node.position.x !== 0) {
        setNodes((current) =>
          current.map((item) =>
            item.id === node.id ? { ...item, position: { x: 0, y: node.position.y } } : item
          )
        );
      }
    },
    [readOnly, setNodes]
  );

  const onNodeDragStop = useCallback(
    (_: unknown, node: EditorNode) => {
      if (readOnly) return;

      if (node.type === "lane") {
        const laneId = (node.data as { laneId?: string }).laneId;
        if (!laneId || !lanes.length) return;
        const targetIndex = laneIndexFromDragY(lanes, laneId, node.position.y);
        const nextValue = reorderLanes(value, laneId, targetIndex);
        onChange?.(nextValue);
        return;
      }

      const data = node.data as BpmnNodeData;
      const snapped = snapNodeToLane(
        {
          id: node.id,
          type: data.nodeType,
          label: data.label,
          position: node.position,
          lane_id: undefined,
        },
        lanes
      );
      const nextNodes = nodes.map((item) =>
        item.id === node.id ? { ...item, position: snapped.position } : item
      );
      setNodes(nextNodes);
      emitChange(nextNodes, edges);
    },
    [edges, emitChange, lanes, nodes, onChange, readOnly, setNodes, value]
  );

  const addNode = (type: FlowchartNodeType) => {
    if (readOnly) return;
    const id = createNodeId(type.slice(0, 3));
    const paletteLabel =
      FLOWCHART_NODE_PALETTE.find((item) => item.type === type)?.label ?? "Nó";
    const laneId = activeLaneId ?? lanes[0]?.id;
    const countInLane = nodes.filter((node) => {
      if (node.type === "lane" || !laneId) return false;
      const data = node.data as BpmnNodeData;
      return (
        snapNodeToLane(
          {
            id: node.id,
            type: data.nodeType,
            label: data.label,
            position: node.position,
          },
          lanes
        ).lane_id === laneId
      );
    }).length;

    const position =
      laneId && lanes.length
        ? defaultNodePosition(lanes, laneId, countInLane)
        : { x: 80 + nodes.length * 24, y: 80 + nodes.length * 16 };

    const nextNodes: EditorNode[] = [
      ...nodes,
      {
        id,
        type: "flowchart",
        position,
        zIndex: 1,
        data: {
          label: paletteLabel,
          nodeType: type,
          manual: type === "process",
        } satisfies BpmnNodeData,
      },
    ];
    setNodes(nextNodes);
    emitChange(nextNodes, edges);
  };

  const addLane = () => {
    if (readOnly) return;
    const lane = {
      id: createLaneId(),
      label: `Faixa ${(value.lanes?.length ?? 0) + 1}`,
      height: 168,
      order: value.lanes?.length ?? 0,
    };
    const next: FlowchartV1 = {
      ...value,
      lanes: [...(value.lanes ?? []), lane],
    };
    setActiveLaneId(lane.id);
    onChange?.(next);
  };

  const removeActiveLane = async () => {
    if (readOnly || !activeLaneId || !lanes.length) return;
    const lane = lanes.find((item) => item.id === activeLaneId);
    const isLastLane = lanes.length === 1;
    const confirmed = await confirm({
      title: "Remover faixa",
      message: isLastLane
        ? `Remover a faixa «${lane?.label ?? "Faixa"}»? O diagrama volta ao canvas simples, sem swimlanes.`
        : `Remover a faixa «${lane?.label ?? "Faixa"}»? Os nós serão realocados na faixa restante.`,
      confirmLabel: "Remover",
      variant: "danger",
    });
    if (!confirmed) return;
    const next = removeLane(value, activeLaneId);
    onChange?.(next);
    setActiveLaneId(normalizeLanes(next.lanes)[0]?.id);
  };

  const runAutoLayout = () => {
    if (readOnly) return;
    onChange?.(autoLayoutFlowchart(value));
  };

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      if (readOnly) return;
      const deletedIds = new Set(
        deleted.filter((node) => node.type !== "lane").map((node) => node.id)
      );
      if (!deletedIds.size) return;
      const nextNodes = nodes.filter((node) => !deletedIds.has(node.id));
      const nextEdges = edges.filter(
        (edge) => !deletedIds.has(edge.source) && !deletedIds.has(edge.target)
      );
      setNodes(nextNodes);
      setEdges(nextEdges);
      emitChange(nextNodes, nextEdges);
    },
    [edges, emitChange, nodes, readOnly, setEdges, setNodes]
  );

  const onEdgesDelete = useCallback(
    (deleted: Edge[]) => {
      if (readOnly) return;
      const deletedIds = new Set(deleted.map((edge) => edge.id));
      const nextEdges = edges.filter((edge) => !deletedIds.has(edge.id));
      setEdges(nextEdges);
      emitChange(nodes, nextEdges);
    },
    [edges, emitChange, nodes, readOnly, setEdges]
  );

  const applyTemplate = (kind: "linear" | "decision" | "swimlanes") => {
    if (readOnly) return;
    const template =
      kind === "linear"
        ? applyLinearTemplate()
        : kind === "decision"
          ? applyDecisionTemplate()
          : applySwimlaneBpmnTemplate();
    onChange?.(template);
  };

  const nudgeSelection = useCallback(
    (dx: number, dy: number) => {
      if (readOnly || !selectedNodeIds.length) return;
      const selectedIds = new Set(selectedNodeIds);
      const nextNodes = nodes.map((node) => {
        if (node.type === "lane" || !selectedIds.has(node.id)) return node;
        return {
          ...node,
          position: {
            x: node.position.x + dx,
            y: node.position.y + dy,
          },
        };
      });
      setNodes(nextNodes);
      emitChange(nextNodes, edges);
    },
    [edges, emitChange, nodes, readOnly, selectedNodeIds, setNodes]
  );

  const deleteSelection = useCallback(() => {
    if (readOnly || !hasSelection) return;
    if (selectedNodeIds.length) {
      const deletedIds = new Set(selectedNodeIds);
      const nextNodes = nodes.filter((node) => !deletedIds.has(node.id));
      const nextEdges = edges.filter(
        (edge) => !deletedIds.has(edge.source) && !deletedIds.has(edge.target)
      );
      setNodes(nextNodes);
      setEdges(nextEdges);
      emitChange(nextNodes, nextEdges);
      return;
    }
    const deletedEdgeIds = new Set(selectedEdgeIds);
    const nextEdges = edges.filter((edge) => !deletedEdgeIds.has(edge.id));
    setEdges(nextEdges);
    emitChange(nodes, nextEdges);
  }, [
    edges,
    emitChange,
    hasSelection,
    nodes,
    readOnly,
    selectedEdgeIds,
    selectedNodeIds,
    setEdges,
    setNodes,
  ]);

  const copySelection = useCallback(() => {
    if (readOnly || !hasNodeSelection) return;
    const selectedIds = new Set(selectedNodeIds);
    clipboardRef.current = {
      nodes: nodes.filter(
        (node): node is ActivityNode => node.type !== "lane" && selectedIds.has(node.id)
      ),
      edges: edges.filter(
        (edge) => selectedIds.has(edge.source) && selectedIds.has(edge.target)
      ),
    };
  }, [edges, hasNodeSelection, nodes, readOnly, selectedNodeIds]);

  const duplicateSelection = useCallback(() => {
    if (readOnly || !hasNodeSelection) return;
    const selectedIds = new Set(selectedNodeIds);
    const idMap = new Map<string, string>();
    const duplicatedNodes: ActivityNode[] = nodes
      .filter((node): node is ActivityNode => node.type !== "lane" && selectedIds.has(node.id))
      .map((node) => {
        const data = node.data as BpmnNodeData;
        const newId = createNodeId(data.nodeType.slice(0, 3));
        idMap.set(node.id, newId);
        return {
          ...node,
          id: newId,
          selected: true,
          position: {
            x: node.position.x + DUPLICATE_OFFSET,
            y: node.position.y + DUPLICATE_OFFSET,
          },
        };
      });

    if (!duplicatedNodes.length) return;

    const duplicatedEdges = edges
      .filter((edge) => selectedIds.has(edge.source) && selectedIds.has(edge.target))
      .map((edge) => ({
        ...edge,
        id: createEdgeId(),
        source: idMap.get(edge.source) ?? edge.source,
        target: idMap.get(edge.target) ?? edge.target,
        selected: false,
        data: {
          readOnly,
          onLabelChange: readOnly ? undefined : handleEdgeLabelChange,
        },
      }));

    const nextNodes = [
      ...nodes.map((node) => ({ ...node, selected: false })),
      ...duplicatedNodes,
    ];
    const nextEdges = [...edges, ...duplicatedEdges];
    setNodes(nextNodes);
    setEdges(nextEdges);
    emitChange(nextNodes, nextEdges);
  }, [
    edges,
    emitChange,
    handleEdgeLabelChange,
    hasNodeSelection,
    nodes,
    readOnly,
    selectedNodeIds,
    setEdges,
    setNodes,
  ]);

  useEffect(() => {
    if (readOnly || !hasNodeSelection) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, [contenteditable='true']")) return;

      const dx =
        event.key === "ArrowLeft" ? -NUDGE_STEP : event.key === "ArrowRight" ? NUDGE_STEP : 0;
      const dy =
        event.key === "ArrowUp" ? -NUDGE_STEP : event.key === "ArrowDown" ? NUDGE_STEP : 0;
      if (!dx && !dy) return;
      event.preventDefault();
      nudgeSelection(dx, dy);
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasNodeSelection, nudgeSelection, readOnly]);

  const runSelectionAction = (actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]) => {
    if (actionId === "delete") deleteSelection();
    else if (actionId === "move") canvasWrapperRef.current?.focus();
    else if (actionId === "copy") copySelection();
    else if (actionId === "duplicate") duplicateSelection();
  };

  const isSelectionActionDisabled = (
    actionId: (typeof DIAGRAM_EDITOR_SELECTION_ACTIONS)[number]["id"]
  ) => {
    if (actionId === "delete") return !hasSelection;
    if (actionId === "move" || actionId === "copy" || actionId === "duplicate") {
      return !hasNodeSelection;
    }
    return false;
  };

  const runEditorAction = (actionId: (typeof DIAGRAM_EDITOR_ACTIONS)[number]["id"]) => {
    if (actionId === "addLane") addLane();
    else if (actionId === "autoLayout") runAutoLayout();
    else if (actionId === "templateLinear") applyTemplate("linear");
    else if (actionId === "templateDecision") applyTemplate("decision");
    else if (actionId === "templateSwimlanes") applyTemplate("swimlanes");
  };

  return (
    <div
      className={[
        "tm-diagram-editor",
        layout === "fill" ? "tm-diagram-editor--fill" : "",
        "tm-diagram-editor--overlay-tools",
      ]
        .filter(Boolean)
        .join(" ")}
      ref={exportRef}
    >
      <TabPanelTransition tabKey={activeTab}>
        {activeTab === "canvas" ? (
          <div
            className="tm-diagram-editor__stage"
            style={{ minHeight: canvasHeight }}
          >
            {!readOnly && showTemplates ? (
              <FlowchartEditorToolbar
                toolbarTab={toolbarTab}
                onToolbarTabChange={setToolbarTab}
                lanes={lanes}
                activeLaneId={activeLaneId}
                onActiveLaneChange={setActiveLaneId}
                onRemoveLane={removeActiveLane}
                onAddNode={addNode}
                onEditorAction={runEditorAction}
              />
            ) : null}

            {!readOnly ? (
              <FlowchartEditorActionDock
                onSelectionAction={runSelectionAction}
                isSelectionActionDisabled={isSelectionActionDisabled}
              />
            ) : null}

            {showPreviewTab ? (
              <div className="tm-diagram-editor__view-tabs tm-diagram-editor__view-tabs--overlay">
                <HelpTooltip
                  content={TM_HELP_TOOLTIPS.diagramEditor.canvasTab}
                  ariaLabel="Ajuda: Canvas"
                  wrap
                  placement="bottom"
                  className="tm-diagram-editor__tab-wrap"
                >
                  <button
                    type="button"
                    className={
                      activeTab === "canvas"
                        ? "tm-diagram-editor__tab is-active"
                        : "tm-diagram-editor__tab"
                    }
                    onClick={() => setActiveTab("canvas")}
                  >
                    Canvas
                  </button>
                </HelpTooltip>
                <HelpTooltip
                  content={TM_HELP_TOOLTIPS.diagramEditor.mermaidTab}
                  ariaLabel="Ajuda: Preview Mermaid"
                  wrap
                  placement="bottom"
                  className="tm-diagram-editor__tab-wrap"
                >
                  <button
                    type="button"
                    className="tm-diagram-editor__tab"
                    onClick={() => switchToMermaidTab()}
                  >
                    Mermaid
                  </button>
                </HelpTooltip>
              </div>
            ) : null}

            <div
              ref={canvasWrapperRef}
              tabIndex={readOnly ? -1 : 0}
              className={[
                "tm-diagram-editor__canvas",
                lanes.length ? "tm-diagram-editor__canvas--swimlanes" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={{ height: canvasHeight }}
            >
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                colorMode={colorMode}
                defaultEdgeOptions={{
                  type: "flowchart",
                  labelStyle: { fontSize: 11, fontWeight: 600 },
                  labelBgStyle: { fillOpacity: 0.92 },
                }}
                onInit={(instance) => {
                  window.requestAnimationFrame(() => {
                    void instance.fitView({ padding: 0.15, duration: 0 });
                  });
                }}
                onNodesChange={readOnly ? undefined : onNodesChange}
                onEdgesChange={readOnly ? undefined : onEdgesChange}
                onConnect={onConnect}
                onNodeDrag={onNodeDrag}
                onNodeDragStop={onNodeDragStop}
                onNodesDelete={onNodesDelete}
                onEdgesDelete={onEdgesDelete}
                deleteKeyCode={readOnly ? null : ["Delete", "Backspace"]}
                minZoom={0.2}
                maxZoom={1.5}
                nodesDraggable={!readOnly}
                nodesConnectable={!readOnly}
                elementsSelectable={!readOnly}
                proOptions={{ hideAttribution: true }}
              >
                <Background gap={20} size={1} />
                <MiniMap pannable zoomable />
                <Controls showInteractive={!readOnly} position="bottom-left" />
              </ReactFlow>
            </div>
          </div>
        ) : (
          <>
            {showPreviewTab ? (
              <div className="tm-diagram-editor__view-tabs">
                <HelpTooltip
                  content={TM_HELP_TOOLTIPS.diagramEditor.canvasTab}
                  ariaLabel="Ajuda: Canvas"
                  wrap
                  placement="bottom"
                  className="tm-diagram-editor__tab-wrap"
                >
                  <button
                    type="button"
                    className="tm-diagram-editor__tab"
                    onClick={() => setActiveTab("canvas")}
                  >
                    Canvas
                  </button>
                </HelpTooltip>
                <HelpTooltip
                  content={TM_HELP_TOOLTIPS.diagramEditor.mermaidTab}
                  ariaLabel="Ajuda: Preview Mermaid"
                  wrap
                  placement="bottom"
                  className="tm-diagram-editor__tab-wrap"
                >
                  <button
                    type="button"
                    className={
                      activeTab === "mermaid"
                        ? "tm-diagram-editor__tab is-active"
                        : "tm-diagram-editor__tab"
                    }
                    onClick={() => switchToMermaidTab()}
                  >
                    Mermaid
                  </button>
                </HelpTooltip>
              </div>
            ) : null}
            <FlowchartMermaidPanel
              draft={mermaidDraft}
              onDraftChange={setMermaidDraft}
              onApply={applyMermaidDraft}
              onRefreshFromCanvas={refreshMermaidFromCanvas}
              onUseTemplate={useMermaidTemplate}
              readOnly={readOnly}
              layout={layout}
              applyError={mermaidApplyError}
              applying={mermaidApplying}
              isEmpty={!value.nodes.length}
            />
          </>
        )}
      </TabPanelTransition>
    </div>
  );
}

export function FlowchartEditor(props: FlowchartEditorProps) {
  return (
    <ReactFlowProvider>
      <FlowchartEditorInner {...props} />
    </ReactFlowProvider>
  );
}
