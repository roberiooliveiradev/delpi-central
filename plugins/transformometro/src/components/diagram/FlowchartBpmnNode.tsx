import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { User } from "lucide-react";

import type { FlowchartNodeType } from "../../types/diagram";

export type BpmnNodeData = {
  label: string;
  nodeType: FlowchartNodeType;
  highlight?: string;
  manual?: boolean;
  readOnly?: boolean;
  inScope?: boolean;
  scopeSelectable?: boolean;
  onToggleScope?: (nodeId: string) => void;
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

export function FlowchartBpmnNode({ id, data }: NodeProps<Node<BpmnNodeData>>) {
  const scopeCheckbox = data.scopeSelectable ? (
    <label className="tm-diagram-node__scope">
      <input
        type="checkbox"
        checked={Boolean(data.inScope)}
        onChange={() => data.onToggleScope?.(id)}
      />
    </label>
  ) : null;

  if (data.nodeType === "start") {
    return (
      <div className="tm-diagram-node-wrap tm-diagram-node-wrap--start">
        <ConnectionHandles />
        <div className={nodeClassName("start", data.highlight)}>
          <span className="tm-diagram-node__start-dot" aria-hidden />
        </div>
        <span className="tm-diagram-node__external-label">{data.label}</span>
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
        <span className="tm-diagram-node__external-label">{data.label}</span>
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
        <span className="tm-diagram-node__external-label tm-diagram-node__external-label--below">
          {data.label}
        </span>
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
      <span className="tm-diagram-node__label">{data.label}</span>
    </div>
  );
}
