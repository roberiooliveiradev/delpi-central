import { Briefcase, User } from "lucide-react";
import { memo, useEffect, useMemo, type CSSProperties, type MouseEvent } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { layoutOrgMembershipForest } from "./layoutOrgMembershipForest";
import {
  orgMembershipFlowBemClasses,
  type OrgMembershipFlowClassNames,
  type OrgMembershipFlowModelEdge,
  type OrgMembershipFlowModelNode,
  type OrgMembershipFlowNodeClick,
  type OrgMembershipFlowNodeData,
} from "./orgMembershipFlowTypes";

export type {
  OrgMembershipFlowClassNames,
  OrgMembershipFlowModelEdge,
  OrgMembershipFlowModelNode,
  OrgMembershipFlowNodeClick,
  OrgMembershipFlowNodeData,
  OrgMembershipNodeKind,
  OrgMembershipNodeTone,
} from "./orgMembershipFlowTypes";

export { layoutOrgMembershipForest } from "./layoutOrgMembershipForest";
export { orgMembershipFlowBemClasses };

type FlowNode = Node<OrgMembershipFlowNodeData, "orgMembership">;

type OrgMembershipNodeViewProps = NodeProps<FlowNode> & {
  classNames: OrgMembershipFlowClassNames;
};

function OrgMembershipNodeView({ data, classNames }: OrgMembershipNodeViewProps) {
  const Icon = data.kind === "portfolio" ? Briefcase : User;
  const toneClass =
    data.tone === "muted"
      ? classNames.nodeMuted
      : data.tone === "warning"
        ? classNames.nodeWarning
        : "";
  const kindClass =
    data.kind === "portfolio" ? classNames.nodePortfolio : classNames.nodePerson;
  return (
    <div
      className={[classNames.node, kindClass, toneClass].filter(Boolean).join(" ")}
      title={data.subtitle ? `${data.title} — ${data.subtitle}` : data.title}
    >
      <Handle type="target" position={Position.Top} className="delpi-ui-org-flow__handle" />
      <span className={classNames.nodeIcon} aria-hidden="true">
        <Icon size={18} strokeWidth={2} />
      </span>
      <div className={classNames.nodeBody}>
        <strong className={classNames.nodeTitle}>{data.title}</strong>
        {data.subtitle ? (
          <span className={classNames.nodeSubtitle}>{data.subtitle}</span>
        ) : null}
      </div>
      <Handle type="source" position={Position.Bottom} className="delpi-ui-org-flow__handle" />
    </div>
  );
}

function FitViewOnChange({ revision }: { revision: string }) {
  const { fitView } = useReactFlow();
  useEffect(() => {
    const id = window.setTimeout(() => {
      void fitView({ padding: 0.18, duration: 200 });
    }, 40);
    return () => window.clearTimeout(id);
  }, [fitView, revision]);
  return null;
}

export type OrgMembershipFlowProps = {
  nodes: readonly OrgMembershipFlowModelNode[];
  edges: readonly OrgMembershipFlowModelEdge[];
  classNames: OrgMembershipFlowClassNames;
  emptyMessage?: string;
  className?: string;
  style?: CSSProperties;
  "aria-label"?: string;
  onNodeClick?: (payload: OrgMembershipFlowNodeClick) => void;
};

function OrgMembershipFlowInner({
  nodes,
  edges,
  classNames,
  emptyMessage = "Nenhum vínculo para exibir.",
  className,
  style,
  "aria-label": ariaLabel = "Organização",
  onNodeClick,
}: OrgMembershipFlowProps) {
  const positions = useMemo(
    () => layoutOrgMembershipForest(nodes, edges),
    [nodes, edges],
  );

  const flowNodes: FlowNode[] = useMemo(
    () =>
      nodes.map((node) => {
        const position = positions.get(node.id) ?? { x: 0, y: 0 };
        return {
          id: node.id,
          type: "orgMembership" as const,
          position,
          data: {
            kind: node.kind,
            entityId: node.entityId,
            title: node.title,
            subtitle: node.subtitle,
            tone: node.tone,
          },
          draggable: false,
          connectable: false,
        };
      }),
    [nodes, positions],
  );

  const flowEdges: Edge[] = useMemo(
    () =>
      edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        selectable: false,
        focusable: false,
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
      })),
    [edges],
  );

  const nodeTypes = useMemo(
    () => ({
      orgMembership: (props: NodeProps<FlowNode>) => (
        <OrgMembershipNodeView {...props} classNames={classNames} />
      ),
    }),
    [classNames],
  );

  const revision = `${nodes.map((n) => n.id).join(",")}|${edges.map((e) => e.id).join(",")}`;

  if (nodes.length === 0) {
    return (
      <div
        className={[classNames.root, className].filter(Boolean).join(" ")}
        style={style}
        role="status"
        aria-label={ariaLabel}
      >
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  const handleNodeClick = (_event: MouseEvent, node: FlowNode) => {
    onNodeClick?.({
      id: node.id,
      kind: node.data.kind,
      entityId: node.data.entityId,
    });
  };

  return (
    <div
      className={[classNames.root, className].filter(Boolean).join(" ")}
      style={style}
      aria-label={ariaLabel}
    >
      <div className={classNames.canvas}>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          edgesFocusable={false}
          panOnScroll
          zoomOnScroll
          fitView
          minZoom={0.35}
          maxZoom={1.6}
          proOptions={{ hideAttribution: true }}
          onNodeClick={handleNodeClick}
        >
          <Background gap={18} size={1} />
          <Controls showInteractive={false} />
          <MiniMap pannable zoomable nodeStrokeWidth={2} />
          <FitViewOnChange revision={revision} />
        </ReactFlow>
      </div>
    </div>
  );
}

export function OrgMembershipFlow(props: OrgMembershipFlowProps) {
  return (
    <ReactFlowProvider>
      <OrgMembershipFlowInner {...props} />
    </ReactFlowProvider>
  );
}

export type DashboardOrgMembershipFlowProps = Omit<OrgMembershipFlowProps, "classNames">;

export function createDashboardOrgMembershipFlow(config: { prefix: string }) {
  const classNames = orgMembershipFlowBemClasses(config.prefix);
  const DashboardOrgMembershipFlow = memo(function DashboardOrgMembershipFlow(
    props: DashboardOrgMembershipFlowProps,
  ) {
    return <OrgMembershipFlow classNames={classNames} {...props} />;
  });
  DashboardOrgMembershipFlow.displayName = "DashboardOrgMembershipFlow";
  return DashboardOrgMembershipFlow;
}
