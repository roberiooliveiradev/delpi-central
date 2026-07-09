import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { FileText, Layers, MessageSquare, User } from "lucide-react";
import type { ReactNode } from "react";

import type { FlowchartNodeType } from "../../types/diagram";
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

const HANDLE_STYLE = { width: 7, height: 7, borderRadius: 999, border: "2px solid var(--ds-card-bg)" };

function ConnectionHandles() {
  return (
    <>
      <Handle type="target" position={Position.Left} style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Right} style={HANDLE_STYLE} />
      <Handle type="target" position={Position.Top} id="top-target" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Bottom} id="bottom-source" style={HANDLE_STYLE} />
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
  if (!data.scopeSelectable) {
    return null;
  }

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
}: {
  shellClassName?: string;
  children: ReactNode;
}) {
  return (
    <div className={["tm-diagram-node-shell", shellClassName].filter(Boolean).join(" ")}>
      <ConnectionHandles />
      {children}
    </div>
  );
}

export function FlowchartBpmnNode({ id, data }: NodeProps<Node<BpmnNodeData>>) {
  const scopeCheckbox = <ScopeCheckbox id={id} data={data} />;

  if (data.nodeType === "start") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--event">
        <NodeShell shellClassName="tm-diagram-node-shell--event">
          <span className="tm-diagram-node__start-dot" aria-hidden />
        </NodeShell>
        <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "end") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--event">
        <NodeShell shellClassName="tm-diagram-node-shell--event">
          <span className="tm-diagram-node__end-ring" aria-hidden />
        </NodeShell>
        <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "decision") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--decision">
        <NodeShell shellClassName="tm-diagram-node-shell--decision">
          <div className={nodeClassName("decision", data.highlight)}>
            <span className="tm-diagram-node__gateway-x" aria-hidden>
              ×
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

  if (data.nodeType === "document") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
        <NodeShell shellClassName="tm-diagram-node-shell--box">
          <div className={nodeClassName("document", data.highlight)}>
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

  if (data.nodeType === "data") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--data">
        <NodeShell shellClassName="tm-diagram-node-shell--data">
          <div className={nodeClassName("data", data.highlight)}>
            <div className="tm-diagram-node__data-cylinder">
              <div className="tm-diagram-node__data-rim tm-diagram-node__data-rim--top" aria-hidden />
              <div className="tm-diagram-node__data-body">
                <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
              </div>
              <div className="tm-diagram-node__data-rim tm-diagram-node__data-rim--bottom" aria-hidden />
            </div>
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "subprocess") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
        <NodeShell shellClassName="tm-diagram-node-shell--box">
          <div className={nodeClassName("subprocess", data.highlight)}>
            <span className="tm-diagram-node__subprocess-inner" aria-hidden />
            <span className="tm-diagram-node__shape-icon" aria-hidden>
              <Layers size={13} strokeWidth={2.2} />
            </span>
            <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
          </div>
        </NodeShell>
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "comment") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--comment">
        <NodeShell shellClassName="tm-diagram-node-shell--comment">
          <div className={nodeClassName("comment", data.highlight)}>
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

  return (
    <div className="tm-diagram-node-wrap tm-diagram-node-wrap--box">
      <NodeShell shellClassName="tm-diagram-node-shell--box">
        <div className={nodeClassName(data.nodeType, data.highlight)}>
          {data.manual !== false && data.nodeType === "process" ? (
            <span className="tm-diagram-node__icon" aria-hidden>
              <User size={12} strokeWidth={2.2} />
            </span>
          ) : null}
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
      </NodeShell>
      {scopeCheckbox}
    </div>
  );
}
