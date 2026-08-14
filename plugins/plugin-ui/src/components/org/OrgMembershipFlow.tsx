import { Briefcase, UsersRound } from "lucide-react";
import {
  memo,
  useEffect,
  useMemo,
  type CSSProperties,
  type MouseEvent,
} from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useNodesInitialized,
  useReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { withBemModifier } from "../../utils/delpiUiClass";
import { useDelpiDarkMode } from "../bpmn/hooks/useDelpiDarkMode";
import { DiagramFullscreenFrame } from "../bpmn/shell/DiagramFullscreenFrame";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
} from "../layout/InitialsAvatar";
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

const PERSON_AVATAR_CLASS_NAMES = initialsAvatarBemClasses("delpi-ui");

type FlowNode = Node<OrgMembershipFlowNodeData, "orgMembership">;

type OrgMembershipNodeViewProps = NodeProps<FlowNode> & {
  classNames: OrgMembershipFlowClassNames;
};

function OrgMembershipNodeView({ data, classNames }: OrgMembershipNodeViewProps) {
  const Icon = data.kind === "portfolio" ? Briefcase : UsersRound;
  const toneClass =
    data.tone === "muted"
      ? classNames.nodeMuted
      : data.tone === "warning"
        ? classNames.nodeWarning
        : "";
  const kindClass =
    data.kind === "portfolio"
      ? classNames.nodePortfolio
      : data.kind === "group"
        ? classNames.nodeGroup
        : classNames.nodePerson;
  return (
    <div
      className={[classNames.node, kindClass, toneClass].filter(Boolean).join(" ")}
      title={data.subtitle ? `${data.title} — ${data.subtitle}` : data.title}
    >
      <Handle type="target" position={Position.Top} className="delpi-ui-org-flow__handle" />
      <span
        className={[
          classNames.nodeIcon,
          data.kind === "person" ? "delpi-ui-org-flow__node-icon--avatar" : null,
        ]
          .filter(Boolean)
          .join(" ")}
        aria-hidden="true"
      >
        {data.kind === "person" ? (
          <InitialsAvatar
            name={data.title}
            colorKey={data.entityId || data.title}
            src={data.avatarSrc}
            size="sm"
            classNames={PERSON_AVATAR_CLASS_NAMES}
            previewable={false}
          />
        ) : (
          <Icon size={18} strokeWidth={2.25} />
        )}
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

/** Enquadra o grafo após os nós medirem o layout — evita canvas vazio no remount/eixo. */
function FitViewOnChange({ revision }: { revision: string }) {
  const { fitView } = useReactFlow();
  const nodesInitialized = useNodesInitialized();
  useEffect(() => {
    if (!nodesInitialized) return;
    const id = window.setTimeout(() => {
      void fitView({ padding: 0.2, duration: 220 });
    }, 0);
    return () => window.clearTimeout(id);
  }, [fitView, revision, nodesInitialized]);
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
  /** Força tema; default segue `data-theme` Delpi. */
  colorMode?: "light" | "dark";
  /** Botão + modal de tela cheia (kit DiagramFullscreenFrame). Default true. */
  fullscreen?: boolean;
  fullscreenTitle?: string;
  fullscreenSubtitle?: string;
  portalScopeClassName?: string;
};

function OrgMembershipCanvas({
  nodes,
  edges,
  classNames,
  emptyMessage = "Nenhum vínculo para exibir.",
  className,
  style,
  "aria-label": ariaLabel = "Organização",
  onNodeClick,
  colorMode,
}: OrgMembershipFlowProps) {
  const isDarkFromHook = useDelpiDarkMode();
  const isDark = colorMode ? colorMode === "dark" : isDarkFromHook;
  const colorModeAttr = isDark ? "dark" : "light";

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
            avatarSrc: node.avatarSrc,
          },
          draggable: false,
          connectable: false,
        };
      }),
    [nodes, positions],
  );

  const edgeStroke = isDark ? "rgba(148, 163, 184, 0.75)" : "rgba(100, 116, 139, 0.7)";

  const flowEdges: Edge[] = useMemo(
    () =>
      edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        selectable: false,
        focusable: false,
        style: { stroke: edgeStroke, strokeWidth: 1.75 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 18,
          height: 18,
          color: edgeStroke,
        },
      })),
    [edges, edgeStroke],
  );

  const nodeTypes = useMemo(
    () => ({
      orgMembership: (props: NodeProps<FlowNode>) => (
        <OrgMembershipNodeView {...props} classNames={classNames} />
      ),
    }),
    [classNames],
  );

  const revision = `${colorModeAttr}|${nodes
    .map((n) => `${n.id}:${n.avatarSrc ? "1" : "0"}`)
    .join(",")}|${edges.map((e) => e.id).join(",")}`;

  const rootClass = [
    withBemModifier(classNames.root, isDark ? "dark" : "light"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (nodes.length === 0) {
    return (
      <div className={rootClass} style={style} role="status" aria-label={ariaLabel}>
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

  const minimapMask = isDark ? "rgba(15, 23, 42, 0.72)" : "rgba(248, 250, 252, 0.78)";
  const minimapNode = (node: Node) => {
    const kind = (node.data as OrgMembershipFlowNodeData | undefined)?.kind;
    if (kind === "person") return isDark ? "#34d399" : "#059669";
    return isDark ? "#60a5fa" : "#2563eb";
  };

  return (
    <div className={rootClass} style={style} aria-label={ariaLabel} data-color-mode={colorModeAttr}>
      <div className={classNames.canvas}>
        <ReactFlow
          nodes={flowNodes}
          edges={flowEdges}
          nodeTypes={nodeTypes}
          colorMode={colorModeAttr}
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          edgesFocusable={false}
          panOnDrag
          panOnScroll
          zoomOnScroll
          zoomOnPinch
          zoomOnDoubleClick
          fitView
          minZoom={0.25}
          maxZoom={1.85}
          proOptions={{ hideAttribution: true }}
          onNodeClick={handleNodeClick}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1.35}
            color={isDark ? "rgba(148, 163, 184, 0.28)" : "rgba(100, 116, 139, 0.35)"}
          />
          <Controls
            showInteractive={false}
            position="bottom-left"
            aria-label="Controles de zoom e enquadramento"
          />
          <MiniMap
            pannable
            zoomable
            position="bottom-right"
            nodeStrokeWidth={2}
            nodeColor={minimapNode}
            maskColor={minimapMask}
            ariaLabel="Minimapa da organização"
          />
          <FitViewOnChange revision={revision} />
        </ReactFlow>
      </div>
    </div>
  );
}

export function OrgMembershipFlow(props: OrgMembershipFlowProps) {
  const {
    fullscreen = true,
    fullscreenTitle = "Organização",
    fullscreenSubtitle,
    portalScopeClassName,
  } = props;

  const canvas = (
    <ReactFlowProvider>
      <OrgMembershipCanvas {...props} />
    </ReactFlowProvider>
  );

  if (!fullscreen) {
    return canvas;
  }

  return (
    <DiagramFullscreenFrame
      title={fullscreenTitle}
      subtitle={fullscreenSubtitle}
      portalScopeClassName={portalScopeClassName}
      labels={{
        expand: "Tela cheia",
        exit: "Sair da tela cheia",
        expandHint:
          "Abre o organograma em tela cheia. Use pan (arrastar), scroll para zoom e os controles no canto. Esc ou «Sair da tela cheia» para voltar.",
        closeAriaLabel: "Fechar tela cheia",
      }}
    >
      {canvas}
    </DiagramFullscreenFrame>
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
