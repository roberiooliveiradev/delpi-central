import {
  AlertTriangle,
  ArrowRightLeft,
  Ban,
  BookOpen,
  Bot,
  Circle,
  CircleDot,
  Clock,
  Code2,
  Diamond,
  FileText,
  GitBranch,
  Hand,
  Layers,
  Link2,
  Mail,
  MessageSquare,
  Minus,
  Network,
  Plus,
  Radio,
  RotateCcw,
  Send,
  Square,
  Star,
  Timer,
  TrendingUp,
  User,
  Workflow,
  type LucideIcon,
} from "lucide-react";
import { Handle, Position, useViewport, type Node, type NodeProps } from "@xyflow/react";
import type { ReactNode } from "react";

import {
  BPMN_NODE_DEFINITIONS,
  getBpmnNodeDefinition,
  type BpmnMarker,
  type FlowchartNodeType,
} from "../../types/bpmnNodeCatalog";
import { DiagramInlineTextEdit } from "./DiagramInlineTextEdit";

export type BpmnNodeData = {
  label: string;
  nodeType: FlowchartNodeType;
  highlight?: string;
  manual?: boolean;
  readOnly?: boolean;
  inScope?: boolean;
  scopeSelectable?: boolean;
  onToggleScope?: (nodeId: string) => void;
  onLabelChange?: (nodeId: string, label: string) => void;
};

/** Tamanho alvo do handle na tela (px). */
const HANDLE_SCREEN_PX = 15;
const HANDLE_SCREEN_COMPACT_PX = 12;
/** Acima deste zoom, handles mantêm tamanho visual (não encolhem mais na tela). */
const HANDLE_ZOOM_SIZE_CEILING = 1.5;

function resolveHandleFlowSize(screenPx: number, zoom: number): number {
  return screenPx / Math.min(zoom, HANDLE_ZOOM_SIZE_CEILING);
}

const MARKER_ICONS: Partial<Record<BpmnMarker, LucideIcon>> = {
  message: Mail,
  timer: Clock,
  signal: Radio,
  conditional: FileText,
  error: AlertTriangle,
  escalation: TrendingUp,
  compensation: RotateCcw,
  cancel: Ban,
  link: Link2,
  multiple: GitBranch,
  parallel: Network,
  terminate: CircleDot,
  user: User,
  service: Bot,
  manual: Hand,
  script: Code2,
  business_rule: BookOpen,
  send: Send,
  receive: Mail,
  call: Workflow,
  ad_hoc: Star,
  transaction: ArrowRightLeft,
  event_sub: Timer,
};

function ConnectionHandles({ compact = false }: { compact?: boolean }) {
  const { zoom } = useViewport();
  const size = resolveHandleFlowSize(compact ? HANDLE_SCREEN_COMPACT_PX : HANDLE_SCREEN_PX, zoom);
  const style = {
    width: size,
    height: size,
    borderRadius: 999,
    border: "2px solid var(--ds-card-bg)",
  };
  const sides = [
    { position: Position.Left, id: "left" },
    { position: Position.Right, id: "right" },
    { position: Position.Top, id: "top" },
    { position: Position.Bottom, id: "bottom" },
  ] as const;

  return (
    <>
      {sides.flatMap(({ position, id }) => [
        <Handle
          key={`${id}-target`}
          id={`${id}-target`}
          type="target"
          position={position}
          className="tm-diagram-node__handle"
          style={style}
        />,
        <Handle
          key={`${id}-source`}
          id={`${id}-source`}
          type="source"
          position={position}
          className="tm-diagram-node__handle"
          style={style}
        />,
      ])}
    </>
  );
}

function nodeClassName(type: FlowchartNodeType, highlight?: string): string {
  return [
    "tm-diagram-node",
    `tm-diagram-node--${type}`,
    highlight ? `tm-diagram-node--${highlight}` : "",
  ]
    .filter(Boolean)
    .join(" ");
}

function NodeLabel({
  nodeId,
  data,
  className,
  ariaLabel = "Texto do nó",
}: {
  nodeId: string;
  data: BpmnNodeData;
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <DiagramInlineTextEdit
      value={data.label}
      readOnly={data.readOnly}
      onCommit={(next) => data.onLabelChange?.(nodeId, next)}
      className={className}
      ariaLabel={ariaLabel}
      emptyFallback="Texto"
    />
  );
}

function ScopeCheckbox({ id, data }: { id: string; data: BpmnNodeData }) {
  if (!data.scopeSelectable) return null;
  return (
    <label className="tm-diagram-node__scope">
      <input
        type="checkbox"
        checked={Boolean(data.inScope)}
        onChange={() => data.onToggleScope?.(id)}
      />
    </label>
  );
}

function NodeShell({
  shellClassName,
  children,
  compactHandles,
}: {
  shellClassName?: string;
  children: ReactNode;
  compactHandles?: boolean;
}) {
  return (
    <div className={["tm-diagram-node-shell", shellClassName].filter(Boolean).join(" ")}>
      <ConnectionHandles compact={compactHandles} />
      {children}
    </div>
  );
}

function GatewaySymbol({ marker }: { marker: BpmnMarker }) {
  if (marker === "parallel_gateway") return <span className="tm-diagram-node__gateway-glyph tm-diagram-node__gateway-glyph--parallel" aria-hidden>+</span>;
  if (marker === "inclusive") return <span className="tm-diagram-node__gateway-glyph tm-diagram-node__gateway-glyph--inclusive" aria-hidden>O</span>;
  if (marker === "complex") return <span className="tm-diagram-node__gateway-glyph tm-diagram-node__gateway-glyph--complex" aria-hidden>✱</span>;
  if (marker === "event_based") return <span className="tm-diagram-node__gateway-glyph tm-diagram-node__gateway-glyph--event" aria-hidden>◇</span>;
  return <span className="tm-diagram-node__gateway-glyph tm-diagram-node__gateway-glyph--exclusive" aria-hidden>×</span>;
}

function BpmnMarkerGlyph({
  marker,
  size = 14,
  tone = "default",
}: {
  marker: BpmnMarker;
  size?: number;
  tone?: "default" | "start" | "end" | "end-filled" | "intermediate" | "intermediate-throw" | "boundary";
}) {
  if (marker === "none" || marker === "exclusive" || marker === "parallel_gateway" || marker === "inclusive" || marker === "complex" || marker === "event_based") {
    return null;
  }
  const Icon = MARKER_ICONS[marker];
  if (Icon) {
    return (
      <span
        className={[
          "tm-diagram-node__marker-icon",
          tone !== "default" ? `tm-diagram-node__marker-icon--${tone}` : "",
        ]
          .filter(Boolean)
          .join(" ")}
        aria-hidden
      >
        <Icon size={size} strokeWidth={2.4} />
      </span>
    );
  }
  return null;
}

function EventStartShape({ marker }: { marker: BpmnMarker }) {
  return (
    <span
      className={[
        "tm-diagram-node__event-shape",
        "tm-diagram-node__event-shape--start",
        marker !== "none" ? "tm-diagram-node__event-shape--marked" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden
    >
      <BpmnMarkerGlyph marker={marker} size={15} tone="start" />
    </span>
  );
}

function EventEndShape({ marker }: { marker: BpmnMarker }) {
  return (
    <span
      className={[
        "tm-diagram-node__event-shape",
        "tm-diagram-node__event-shape--end",
        marker === "terminate" ? "tm-diagram-node__event-shape--terminate" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden
    >
      <BpmnMarkerGlyph
        marker={marker}
        size={marker === "terminate" ? 12 : 14}
        tone={marker === "terminate" ? "end-filled" : "end"}
      />
    </span>
  );
}

function EventIntermediateShape({
  marker,
  variant,
}: {
  marker: BpmnMarker;
  variant: "catch" | "throw";
}) {
  return (
    <span
      className={[
        "tm-diagram-node__event-shape",
        "tm-diagram-node__event-shape--intermediate",
        variant === "throw" ? "tm-diagram-node__event-shape--throw" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-hidden
    >
      <BpmnMarkerGlyph
        marker={marker}
        size={14}
        tone={variant === "throw" ? "intermediate-throw" : "intermediate"}
      />
    </span>
  );
}

function DataStoreCylinder() {
  return (
    <svg
      className="tm-diagram-node__data-store-svg"
      viewBox="0 0 72 50"
      width="72"
      height="50"
      aria-hidden
    >
      <rect className="tm-diagram-node__data-store-body" x="6" y="12" width="60" height="26" />
      <line className="tm-diagram-node__data-store-edge" x1="6" y1="12" x2="6" y2="38" />
      <line className="tm-diagram-node__data-store-edge" x1="66" y1="12" x2="66" y2="38" />
      <ellipse className="tm-diagram-node__data-store-cap" cx="36" cy="12" rx="30" ry="9" />
      <ellipse className="tm-diagram-node__data-store-base" cx="36" cy="38" rx="30" ry="9" />
    </svg>
  );
}

function BoundaryShape({ marker }: { marker: BpmnMarker }) {
  return (
    <span className="tm-diagram-node__event-shape tm-diagram-node__event-shape--boundary" aria-hidden>
      <BpmnMarkerGlyph marker={marker} size={12} tone="boundary" />
    </span>
  );
}

export function FlowchartBpmnNode({ id, data }: NodeProps<Node<BpmnNodeData>>) {
  const def = getBpmnNodeDefinition(data.nodeType) ?? BPMN_NODE_DEFINITIONS.process;
  const scopeCheckbox = <ScopeCheckbox id={id} data={data} />;
  const externalLabel = (
    <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
  );

  if (def.shape === "event_start") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--event">
        <NodeShell shellClassName="tm-diagram-node-shell--event">
          <EventStartShape marker={def.marker} />
        </NodeShell>
        {externalLabel}
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "event_end") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--event">
        <NodeShell shellClassName="tm-diagram-node-shell--event">
          <EventEndShape marker={def.marker} />
        </NodeShell>
        {externalLabel}
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "event_intermediate_catch" || def.shape === "event_intermediate_throw") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--event">
        <NodeShell shellClassName="tm-diagram-node-shell--event">
          <EventIntermediateShape
            marker={def.marker}
            variant={def.shape === "event_intermediate_throw" ? "throw" : "catch"}
          />
        </NodeShell>
        {externalLabel}
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "boundary") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--boundary">
        <NodeShell shellClassName="tm-diagram-node-shell--boundary" compactHandles>
          <BoundaryShape marker={def.marker} />
        </NodeShell>
        <NodeLabel
          nodeId={id}
          data={data}
          className="tm-diagram-node__external-label tm-diagram-node__external-label--below"
        />
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "gateway") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--decision">
        <NodeShell shellClassName="tm-diagram-node-shell--decision">
          <div className={`${nodeClassName(data.nodeType, data.highlight)} tm-diagram-node--gateway`}>
            <span className="tm-diagram-node__gateway-symbol" aria-hidden>
              <GatewaySymbol marker={def.marker} />
            </span>
          </div>
        </NodeShell>
        <NodeLabel
          nodeId={id}
          data={data}
          className="tm-diagram-node__external-label tm-diagram-node__external-label--below"
        />
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "artifact_document") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
        <NodeShell shellClassName="tm-diagram-node-shell--box">
          <div className={nodeClassName(data.nodeType, data.highlight)}>
            <span className="tm-diagram-node__doc-fold" aria-hidden />
            <span className="tm-diagram-node__shape-icon" aria-hidden>
              <FileText size={13} strokeWidth={2.2} />
            </span>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "artifact_data_store") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--data-store">
        <NodeShell shellClassName="tm-diagram-node-shell--data-store">
          <div className={`${nodeClassName(data.nodeType, data.highlight)} tm-diagram-node--data-store`}>
            <DataStoreCylinder />
          </div>
        </NodeShell>
        <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "artifact_data_object") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--data-object">
        <NodeShell shellClassName="tm-diagram-node-shell--data-object">
          <div className={nodeClassName(data.nodeType, data.highlight)}>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "artifact_comment") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--comment">
        <NodeShell shellClassName="tm-diagram-node-shell--comment">
          <div className={nodeClassName(data.nodeType, data.highlight)}>
            <span className="tm-diagram-node__shape-icon" aria-hidden>
              <MessageSquare size={13} strokeWidth={2.2} />
            </span>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
            <span className="tm-diagram-node__comment-tail" aria-hidden />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  if (def.shape === "artifact_group") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--group">
        <NodeShell shellClassName="tm-diagram-node-shell--group">
          <div className={nodeClassName(data.nodeType, data.highlight)}>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  const activityClass =
    def.shape === "activity_subprocess"
      ? "subprocess"
      : def.shape === "activity_call"
        ? "call_activity"
        : def.shape === "activity_ad_hoc"
          ? "subprocess_ad_hoc"
          : def.shape === "activity_transaction"
            ? "subprocess_transaction"
            : def.shape === "activity_event_subprocess"
              ? "subprocess_event"
              : data.nodeType;

  if (def.shape.startsWith("activity_")) {
    const ActivityIcon =
      def.marker === "call"
        ? Workflow
        : def.marker === "ad_hoc"
          ? Star
          : def.marker === "transaction"
            ? ArrowRightLeft
            : def.marker === "event_sub"
              ? Timer
              : Layers;
    const activityToneClass =
      def.shape === "activity_call"
        ? "tm-diagram-node__shape-icon--call"
        : def.shape === "activity_ad_hoc"
          ? "tm-diagram-node__shape-icon--ad-hoc"
          : def.shape === "activity_transaction"
            ? "tm-diagram-node__shape-icon--transaction"
            : def.shape === "activity_event_subprocess"
              ? "tm-diagram-node__shape-icon--event-sub"
              : "tm-diagram-node__shape-icon--subprocess";
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
        <NodeShell shellClassName="tm-diagram-node-shell--box">
          <div className={nodeClassName(activityClass as FlowchartNodeType, data.highlight)}>
            {def.shape === "activity_subprocess" ? (
              <span className="tm-diagram-node__subprocess-inner" aria-hidden />
            ) : null}
            <span className={["tm-diagram-node__shape-icon", activityToneClass].join(" ")} aria-hidden>
              <ActivityIcon size={15} strokeWidth={2.4} />
            </span>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  const showManualIcon =
    data.manual !== false && (def.manualTask || def.marker === "user" || def.marker === "manual");

  return (
    <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
      <NodeShell shellClassName="tm-diagram-node-shell--box">
        <div className={nodeClassName(data.nodeType, data.highlight)}>
          {showManualIcon ? (
            <span className="tm-diagram-node__icon" aria-hidden>
              <User size={12} strokeWidth={2.2} />
            </span>
          ) : def.marker !== "none" ? (
            <span className="tm-diagram-node__icon" aria-hidden>
              <BpmnMarkerGlyph marker={def.marker} size={12} />
            </span>
          ) : null}
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
      </NodeShell>
      {scopeCheckbox}
    </div>
  );
}

export const FLOWCHART_NODE_ICON_FALLBACKS: Partial<Record<FlowchartNodeType, LucideIcon>> = {
  start: CircleDot,
  end: Circle,
  process: Square,
  decision: Diamond,
  document: FileText,
  data: Layers,
  comment: MessageSquare,
  gateway_parallel: Plus,
  gateway_inclusive: Circle,
  gateway_complex: Star,
  gateway_event: Minus,
};
