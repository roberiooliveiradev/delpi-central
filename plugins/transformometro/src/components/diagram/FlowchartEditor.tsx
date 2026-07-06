import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useState, type RefObject } from "react";

import { useTransformometroDarkMode } from "../../hooks/useTransformometroDarkMode";
import {
  autoLayoutFlowchart,
  canvasHeightForLanes,
  defaultNodePosition,
  laneTopOffset,
  normalizeLanes,
  removeLane,
  renameLane,
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
  mermaidPreview?: string;
  exportRef?: RefObject<HTMLDivElement | null>;
};

type ActivityNode = Node<BpmnNodeData>;
type LaneNode = Node<{
  label: string;
  height: number;
  laneId?: string;
  readOnly?: boolean;
  onRename?: (laneId: string, label: string) => void;
}>;
type EditorNode = Node;

const nodeTypes = {
  flowchart: FlowchartBpmnNode,
  lane: FlowchartLaneNode,
};

const LANE_NODE_PREFIX = "__lane__";

function isLaneNodeId(id: string): boolean {
  return id.startsWith(LANE_NODE_PREFIX);
}

function buildLaneNodes(
  lanes: ReturnType<typeof normalizeLanes>,
  options?: {
    readOnly?: boolean;
    onRenameLane?: (laneId: string, label: string) => void;
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
      readOnly: options?.readOnly ?? true,
      onRename: options?.onRenameLane,
    },
    draggable: false,
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
    onRenameLane?: (laneId: string, label: string) => void;
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
    type: edge.routing ?? "smoothstep",
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
  mermaidPreview,
  exportRef,
}: FlowchartEditorProps) {
  const lanes = useMemo(() => normalizeLanes(value.lanes), [value.lanes]);

  const handleRenameLane = useCallback(
    (laneId: string, label: string) => {
      if (readOnly) return;
      onChange?.(renameLane(value, laneId, label));
    },
    [onChange, readOnly, value]
  );

  const laneRenderOptions = useMemo(
    () => ({
      readOnly,
      onRenameLane: readOnly ? undefined : handleRenameLane,
    }),
    [handleRenameLane, readOnly]
  );

  const initial = useMemo(() => toReactFlow(value, laneRenderOptions), [laneRenderOptions, value]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [activeTab, setActiveTab] = useState<"canvas" | "mermaid">("canvas");
  const [activeLaneId, setActiveLaneId] = useState<string | undefined>(lanes[0]?.id);
  const isDark = useTransformometroDarkMode();
  const colorMode = isDark ? "dark" : "light";
  const canvasHeight = canvasHeightForLanes(lanes, lanes.length ? 360 : 420);

  useEffect(() => {
    if (lanes.length && !lanes.some((lane) => lane.id === activeLaneId)) {
      setActiveLaneId(lanes[0]?.id);
    }
  }, [activeLaneId, lanes]);

  useEffect(() => {
    const next = toReactFlow(value, laneRenderOptions);
    setNodes(
      next.nodes.map((node) => {
        if (node.type === "lane") {
          return node;
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
    setEdges(next.edges.map((edge) => ({ ...edge, animated: false })));
  }, [
    value,
    readOnly,
    scopeNodeIds,
    selectedScopeIds,
    onToggleScopeNode,
    diffNodeIds,
    laneRenderOptions,
    setNodes,
    setEdges,
  ]);

  const emitChange = useCallback(
    (nextNodes: EditorNode[], nextEdges: Edge[]) => {
      onChange?.(fromReactFlow(nextNodes, nextEdges, value));
    },
    [onChange, value]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly) return;
      setEdges((current) => {
        const next = addEdge(
          {
            ...connection,
            id: createEdgeId(),
            type: "smoothstep",
            labelStyle: { fontSize: 11, fontWeight: 600 },
            labelBgStyle: { fillOpacity: 0.92 },
          },
          current
        );
        emitChange(nodes, next);
        return next;
      });
    },
    [emitChange, nodes, readOnly, setEdges]
  );

  const onNodeDragStop = useCallback(
    (_: unknown, node: EditorNode) => {
      if (readOnly || node.type === "lane") return;
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
    [edges, emitChange, lanes, nodes, readOnly, setNodes]
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

  const renameActiveLane = () => {
    if (readOnly || !activeLaneId) return;
    const lane = lanes.find((item) => item.id === activeLaneId);
    const nextLabel = window.prompt("Nome da faixa (swimlane)", lane?.label ?? "");
    if (nextLabel == null) return;
    onChange?.(renameLane(value, activeLaneId, nextLabel));
  };

  const removeActiveLane = () => {
    if (readOnly || !activeLaneId || lanes.length <= 1) return;
    const lane = lanes.find((item) => item.id === activeLaneId);
    const confirmed = window.confirm(
      `Remover a faixa «${lane?.label ?? "Faixa"}»? Os nós serão realocados na faixa restante.`
    );
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

  return (
    <div className="tm-diagram-editor" ref={exportRef}>
      {!readOnly && showTemplates ? (
        <div className="tm-diagram-editor__toolbar">
          <div className="tm-diagram-editor__palette">
            {FLOWCHART_NODE_PALETTE.map((item) => (
              <button
                key={item.type}
                type="button"
                className="ds-ghost-btn tm-diagram-editor__palette-btn"
                onClick={() => addNode(item.type)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="tm-diagram-editor__templates">
            {lanes.length ? (
              <>
                <label className="tm-diagram-editor__lane-select">
                  Faixa ativa
                  <select
                    value={activeLaneId ?? ""}
                    onChange={(event) => setActiveLaneId(event.target.value)}
                  >
                    {lanes.map((lane) => (
                      <option key={lane.id} value={lane.id}>
                        {lane.label}
                      </option>
                    ))}
                  </select>
                </label>
                <button type="button" className="ds-ghost-btn" onClick={renameActiveLane}>
                  Renomear faixa
                </button>
                <button
                  type="button"
                  className="ds-ghost-btn"
                  onClick={removeActiveLane}
                  disabled={lanes.length <= 1}
                >
                  Remover faixa
                </button>
              </>
            ) : null}
            <button type="button" className="ds-ghost-btn" onClick={addLane}>
              + Faixa (swimlane)
            </button>
            <button type="button" className="ds-ghost-btn" onClick={runAutoLayout}>
              Auto-layout
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => applyTemplate("linear")}>
              Template linear
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => applyTemplate("decision")}>
              Template com decisão
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              onClick={() => applyTemplate("swimlanes")}
            >
              Template BPMN + swimlanes
            </button>
          </div>
          <p className="tm-diagram-editor__hint ds-hint">
            Duplo clique no nó ou na seta para editar o texto · Delete/Backspace remove seleção
            {lanes.length ? " · Duplo clique no cabeçalho da faixa para renomear" : ""}
          </p>
        </div>
      ) : null}

      {showPreviewTab ? (
        <div className="tm-diagram-editor__tabs">
          <button
            type="button"
            className={
              activeTab === "canvas" ? "tm-diagram-editor__tab is-active" : "tm-diagram-editor__tab"
            }
            onClick={() => setActiveTab("canvas")}
          >
            Canvas
          </button>
          <button
            type="button"
            className={
              activeTab === "mermaid"
                ? "tm-diagram-editor__tab is-active"
                : "tm-diagram-editor__tab"
            }
            onClick={() => setActiveTab("mermaid")}
          >
            Preview Mermaid
          </button>
        </div>
      ) : null}

      {activeTab === "canvas" ? (
        <div
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
            colorMode={colorMode}
            defaultEdgeOptions={{
              type: "smoothstep",
              labelStyle: { fontSize: 11, fontWeight: 600 },
              labelBgStyle: { fillOpacity: 0.92 },
            }}
            onNodesChange={readOnly ? undefined : onNodesChange}
            onEdgesChange={readOnly ? undefined : onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onNodesDelete={onNodesDelete}
            onEdgesDelete={onEdgesDelete}
            deleteKeyCode={readOnly ? null : ["Delete", "Backspace"]}
            onNodeDoubleClick={(_, node) => {
              if (readOnly || node.type === "lane") return;
              const data = node.data as BpmnNodeData;
              const nextLabel = window.prompt("Texto do nó", data.label);
              if (nextLabel == null) return;
              const nextNodes = nodes.map((item) =>
                item.id === node.id
                  ? {
                      ...item,
                      data: { ...(item.data as BpmnNodeData), label: nextLabel.trim() || data.label },
                    }
                  : item
              );
              setNodes(nextNodes);
              emitChange(nextNodes, edges);
            }}
            onEdgeDoubleClick={(_, edge) => {
              if (readOnly) return;
              const nextLabel = window.prompt(
                "Rótulo da conexão (ex.: Sim, Não)",
                typeof edge.label === "string" ? edge.label : ""
              );
              if (nextLabel == null) return;
              const nextEdges = edges.map((item) =>
                item.id === edge.id
                  ? { ...item, label: nextLabel.trim() || undefined }
                  : item
              );
              setEdges(nextEdges);
              emitChange(nodes, nextEdges);
            }}
            fitView
            minZoom={0.2}
            maxZoom={1.5}
            nodesDraggable={!readOnly}
            nodesConnectable={!readOnly}
            elementsSelectable={!readOnly}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={20} size={1} />
            <MiniMap pannable zoomable />
            <Controls showInteractive={!readOnly} />
          </ReactFlow>
        </div>
      ) : (
        <pre className="tm-diagram-editor__mermaid-code">{mermaidPreview ?? "Sem preview."}</pre>
      )}
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
