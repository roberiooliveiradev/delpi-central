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
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useCallback, useEffect, useMemo, useState, type RefObject } from "react";

import {
  FLOWCHART_NODE_PALETTE,
  applyDecisionTemplate,
  applyLinearTemplate,
  createEdgeId,
  createNodeId,
  type FlowchartNodeType,
  type FlowchartV1,
} from "../../types/diagram";

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

type FlowNodeData = {
  label: string;
  nodeType: FlowchartNodeType;
  highlight?: string;
  readOnly?: boolean;
  inScope?: boolean;
  scopeSelectable?: boolean;
  onToggleScope?: (nodeId: string) => void;
};

function nodeClassName(type: FlowchartNodeType, highlight?: string): string {
  return [
    "tm-diagram-node",
    `tm-diagram-node--${type}`,
    highlight ? `tm-diagram-node--${highlight}` : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function FlowchartNodeView({ id, data }: NodeProps<Node<FlowNodeData>>) {
  return (
    <div className={nodeClassName(data.nodeType, data.highlight)}>
      {data.scopeSelectable ? (
        <label className="tm-diagram-node__scope">
          <input
            type="checkbox"
            checked={Boolean(data.inScope)}
            onChange={() => data.onToggleScope?.(id)}
          />
        </label>
      ) : null}
      <span className="tm-diagram-node__label">{data.label}</span>
    </div>
  );
}

const nodeTypes = { flowchart: FlowchartNodeView };

function toReactFlow(value: FlowchartV1): { nodes: Node<FlowNodeData>[]; edges: Edge[] } {
  const nodes: Node<FlowNodeData>[] = value.nodes.map((node) => ({
    id: node.id,
    type: "flowchart",
    position: node.position,
    data: {
      label: node.label,
      nodeType: node.type,
      highlight: node.highlight,
    },
  }));
  const edges: Edge[] = value.edges.map((edge) => ({
    id: edge.id,
    source: edge.from,
    target: edge.to,
    label: edge.label ?? undefined,
  }));
  return { nodes, edges };
}

function fromReactFlow(nodes: Node<FlowNodeData>[], edges: Edge[], base: FlowchartV1): FlowchartV1 {
  return {
    ...base,
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.data.nodeType,
      label: node.data.label,
      position: node.position,
      highlight: node.data.highlight as FlowchartV1["nodes"][number]["highlight"],
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      from: edge.source,
      to: edge.target,
      label: typeof edge.label === "string" ? edge.label : null,
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
  const initial = useMemo(() => toReactFlow(value), [value]);
  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);
  const [activeTab, setActiveTab] = useState<"canvas" | "mermaid">("canvas");

  useEffect(() => {
    const next = toReactFlow(value);
    setNodes(
      next.nodes.map((node) => ({
        ...node,
        draggable: !readOnly,
        selectable: !readOnly,
        data: {
          ...node.data,
          readOnly,
          scopeSelectable: Boolean(onToggleScopeNode) && !readOnly,
          inScope: selectedScopeIds ? selectedScopeIds.has(node.id) : scopeNodeIds?.has(node.id),
          onToggleScope: onToggleScopeNode,
          highlight:
            diffNodeIds?.added?.includes(node.id)
              ? "tobe"
              : diffNodeIds?.changed?.includes(node.id)
                ? "changed"
                : diffNodeIds?.removed?.includes(node.id)
                  ? "removed"
                  : node.data.highlight,
        },
      }))
    );
    setEdges(next.edges.map((edge) => ({ ...edge, animated: false })));
  }, [value, readOnly, scopeNodeIds, selectedScopeIds, onToggleScopeNode, diffNodeIds, setNodes, setEdges]);

  const emitChange = useCallback(
    (nextNodes: Node<FlowNodeData>[], nextEdges: Edge[]) => {
      onChange?.(fromReactFlow(nextNodes, nextEdges, value));
    },
    [onChange, value]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      if (readOnly) return;
      setEdges((current) => {
        const next = addEdge({ ...connection, id: createEdgeId() }, current);
        emitChange(nodes, next);
        return next;
      });
    },
    [emitChange, nodes, readOnly, setEdges]
  );

  const onNodeDragStop = useCallback(() => {
    if (readOnly) return;
    emitChange(nodes, edges);
  }, [emitChange, edges, nodes, readOnly]);

  const addNode = (type: FlowchartNodeType) => {
    if (readOnly) return;
    const id = createNodeId(type.slice(0, 3));
    const paletteLabel = FLOWCHART_NODE_PALETTE.find((item) => item.type === type)?.label ?? "Nó";
    const nextNodes: Node<FlowNodeData>[] = [
      ...nodes,
      {
        id,
        type: "flowchart",
        position: { x: 80 + nodes.length * 24, y: 80 + nodes.length * 16 },
        data: { label: paletteLabel, nodeType: type },
      },
    ];
    setNodes(nextNodes);
    emitChange(nextNodes, edges);
  };

  const applyTemplate = (kind: "linear" | "decision") => {
    if (readOnly) return;
    const template = kind === "linear" ? applyLinearTemplate() : applyDecisionTemplate();
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
            <button type="button" className="ds-ghost-btn" onClick={() => applyTemplate("linear")}>
              Template linear
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => applyTemplate("decision")}>
              Template com decisão
            </button>
          </div>
        </div>
      ) : null}

      {showPreviewTab ? (
        <div className="tm-diagram-editor__tabs">
          <button
            type="button"
            className={activeTab === "canvas" ? "tm-diagram-editor__tab is-active" : "tm-diagram-editor__tab"}
            onClick={() => setActiveTab("canvas")}
          >
            Canvas
          </button>
          <button
            type="button"
            className={activeTab === "mermaid" ? "tm-diagram-editor__tab is-active" : "tm-diagram-editor__tab"}
            onClick={() => setActiveTab("mermaid")}
          >
            Preview Mermaid
          </button>
        </div>
      ) : null}

      {activeTab === "canvas" ? (
        <div className="tm-diagram-editor__canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            onNodesChange={readOnly ? undefined : onNodesChange}
            onEdgesChange={readOnly ? undefined : onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onNodeDoubleClick={(_, node) => {
              if (readOnly) return;
              const nextLabel = window.prompt("Texto do nó", node.data.label);
              if (nextLabel == null) return;
              const nextNodes = nodes.map((item) =>
                item.id === node.id
                  ? { ...item, data: { ...item.data, label: nextLabel.trim() || item.data.label } }
                  : item
              );
              setNodes(nextNodes);
              emitChange(nextNodes, edges);
            }}
            fitView
            nodesDraggable={!readOnly}
            nodesConnectable={!readOnly}
            elementsSelectable={!readOnly}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={16} />
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
