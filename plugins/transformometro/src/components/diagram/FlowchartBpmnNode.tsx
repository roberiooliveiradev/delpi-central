import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { Database, FileText, Layers, MessageSquare, User } from "lucide-react";

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

const HANDLE_STYLE = { width: 8, height: 8, borderRadius: 4 };

function ConnectionHandles() {
  return (
    <>
      <Handle type="target" position={Position.Left} style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Right} style={HANDLE_STYLE} />
      <Handle type="target" position={Position.Top} id="top-target" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Bottom} id="bottom-source" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Top} id="top-source" style={HANDLE_STYLE} />
      <Handle type="target" position={Position.Bottom} id="bottom-target" style={HANDLE_STYLE} />
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

export function FlowchartBpmnNode({ id, data }: NodeProps<Node<BpmnNodeData>>) {
  const scopeCheckbox = <ScopeCheckbox id={id} data={data} />;

  if (data.nodeType === "start") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--start">
        <ConnectionHandles />
        <div className={nodeClassName("start", data.highlight)}>
          <span className="tm-diagram-node__start-dot" aria-hidden />
        </div>
        <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "end") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--end">
        <ConnectionHandles />
        <div className={nodeClassName("end", data.highlight)}>
          <span className="tm-diagram-node__end-ring" aria-hidden />
        </div>
        <NodeLabel nodeId={id} data={data} className="tm-diagram-node__external-label" />
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "decision") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--decision">
        <ConnectionHandles />
        <div className={nodeClassName("decision", data.highlight)}>
          <span className="tm-diagram-node__gateway-x" aria-hidden>
            ×
          </span>
        </div>
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
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--document">
        <ConnectionHandles />
        <div className={nodeClassName("document", data.highlight)}>
          <span className="tm-diagram-node__doc-fold" aria-hidden />
          <span className="tm-diagram-node__shape-icon" aria-hidden>
            <FileText size={14} strokeWidth={2.2} />
          </span>
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "data") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--data">
        <ConnectionHandles />
        <div className={nodeClassName("data", data.highlight)}>
          <span className="tm-diagram-node__data-cap" aria-hidden />
          <span className="tm-diagram-node__shape-icon" aria-hidden>
            <Database size={14} strokeWidth={2.2} />
          </span>
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "subprocess") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--subprocess">
        <ConnectionHandles />
        <div className={nodeClassName("subprocess", data.highlight)}>
          <span className="tm-diagram-node__subprocess-inner" aria-hidden />
          <span className="tm-diagram-node__shape-icon" aria-hidden>
            <Layers size={14} strokeWidth={2.2} />
          </span>
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
        {scopeCheckbox}
      </div>
    );
  }

  if (data.nodeType === "comment") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--comment">
        <ConnectionHandles />
        <div className={nodeClassName("comment", data.highlight)}>
          <span className="tm-diagram-node__comment-tail" aria-hidden />
          <span className="tm-diagram-node__shape-icon" aria-hidden>
            <MessageSquare size={14} strokeWidth={2.2} />
          </span>
          <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
        </div>
        {scopeCheckbox}
      </div>
    );
  }

  return (
    <div className={nodeClassName(data.nodeType, data.highlight)}>
      <ConnectionHandles />
      {scopeCheckbox}
      {data.manual !== false && data.nodeType === "process" ? (
        <span className="tm-diagram-node__icon" aria-hidden>
          <User size={12} strokeWidth={2.2} />
        </span>
      ) : null}
      <NodeLabel nodeId={id} data={data} className="tm-diagram-node__label" />
    </div>
  );
}
