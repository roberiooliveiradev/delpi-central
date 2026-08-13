import { delpiUiClass } from "../../utils/delpiUiClass";

export type OrgMembershipNodeKind = "portfolio" | "person" | "group";

export type OrgMembershipNodeTone = "neutral" | "muted" | "warning";

/** Payload do nó no React Flow. */
export type OrgMembershipFlowNodeData = {
  kind: OrgMembershipNodeKind;
  entityId: string;
  title: string;
  subtitle?: string;
  tone?: OrgMembershipNodeTone;
};

/** Nó lógico (antes do layout / React Flow). */
export type OrgMembershipFlowModelNode = {
  id: string;
  kind: OrgMembershipNodeKind;
  /** Id de negócio (carteira ou usuário) para clique. */
  entityId: string;
  title: string;
  subtitle?: string;
  tone?: OrgMembershipNodeTone;
};

export type OrgMembershipFlowModelEdge = {
  id: string;
  source: string;
  target: string;
};

export type OrgMembershipFlowClassNames = {
  root: string;
  canvas: string;
  empty: string;
  node: string;
  nodePortfolio: string;
  nodePerson: string;
  nodeGroup: string;
  nodeMuted: string;
  nodeWarning: string;
  nodeIcon: string;
  nodeBody: string;
  nodeTitle: string;
  nodeSubtitle: string;
};

export type OrgMembershipFlowNodeClick = {
  id: string;
  kind: OrgMembershipNodeKind;
  entityId: string;
};

export function orgMembershipFlowBemClasses(prefix: string): OrgMembershipFlowClassNames {
  const p = prefix.trim() || "delpi-ui";
  const bem = (suffix: string) =>
    delpiUiClass(`${p}-org-flow${suffix}`, `delpi-ui-org-flow${suffix}`);
  return {
    root: bem(""),
    canvas: bem("__canvas"),
    empty: bem("__empty"),
    node: bem("__node"),
    nodePortfolio: bem("__node--portfolio"),
    nodePerson: bem("__node--person"),
    nodeGroup: bem("__node--group"),
    nodeMuted: bem("__node--muted"),
    nodeWarning: bem("__node--warning"),
    nodeIcon: bem("__node-icon"),
    nodeBody: bem("__node-body"),
    nodeTitle: bem("__node-title"),
    nodeSubtitle: bem("__node-subtitle"),
  };
}
