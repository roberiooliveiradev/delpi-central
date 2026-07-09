import {
  AlertTriangle,
  ArrowRightLeft,
  Ban,
  BookOpen,
  Bot,
  Circle,
  CircleDot,
  ClipboardPaste,
  Clock,
  Code2,
  Copy,
  CopyPlus,
  Database,
  Diamond,
  FileText,
  GitBranch,
  GitCompareArrows,
  Hand,
  Layers,
  LayoutGrid,
  Link2,
  Mail,
  MessageSquare,
  Minus,
  Network,
  Plus,
  Radio,
  RotateCcw,
  Rows3,
  Send,
  Square,
  Star,
  Timer,
  Trash2,
  TrendingUp,
  User,
  Wand2,
  Workflow,
  type LucideIcon,
} from "lucide-react";

import type { FlowchartEditorLabels } from "./types/flowchartEditorLabels";
import {
  BPMN_NODE_DEFINITIONS,
  BPMN_PALETTE_CATEGORIES,
  paletteByCategory,
  type BpmnMarker,
  type BpmnPaletteCategoryId,
  type FlowchartNodeType,
} from "./types/bpmnNodeCatalog";

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
  exclusive: Diamond,
  parallel_gateway: Plus,
  inclusive: Circle,
  complex: Star,
  event_based: Minus,
};

const SHAPE_ICONS: Partial<Record<string, LucideIcon>> = {
  event_start: CircleDot,
  event_end: Circle,
  event_intermediate_catch: Circle,
  event_intermediate_throw: CircleDot,
  gateway: Diamond,
  task: Square,
  activity_subprocess: Layers,
  activity_call: Workflow,
  activity_ad_hoc: Star,
  activity_transaction: ArrowRightLeft,
  activity_event_subprocess: Timer,
  artifact_document: FileText,
  artifact_data_store: Database,
  artifact_data_object: FileText,
  artifact_comment: MessageSquare,
  artifact_group: LayoutGrid,
  boundary: Clock,
};

export const FLOWCHART_NODE_ICONS: Record<FlowchartNodeType, LucideIcon> = Object.fromEntries(
  (Object.keys(BPMN_NODE_DEFINITIONS) as FlowchartNodeType[]).map((type) => {
    const def = BPMN_NODE_DEFINITIONS[type];
    const icon =
      MARKER_ICONS[def.marker] ??
      SHAPE_ICONS[def.shape] ??
      (type.startsWith("start") ? CircleDot : type.startsWith("end") ? Circle : Square);
    return [type, icon];
  })
) as Record<FlowchartNodeType, LucideIcon>;

export function flowchartNodeHint(type: FlowchartNodeType, labels: FlowchartEditorLabels): string {
  return labels.nodeHints[type] ?? BPMN_NODE_DEFINITIONS[type]?.label ?? "";
}

export type FlowchartElementGroupTab =
  | "events"
  | "gateways"
  | "tasks"
  | "activities"
  | "artifacts"
  | "boundary"
  | "lanes";

export function flowchartElementGroupTabs(labels: FlowchartEditorLabels) {
  return labels.elementGroupTabs as Array<{ id: FlowchartElementGroupTab; label: string }>;
}

export function flowchartEventSubTabs(labels: FlowchartEditorLabels) {
  return labels.eventSubTabs as Array<{ id: BpmnPaletteCategoryId; label: string }>;
}

export function resolvePaletteCategory(
  group: FlowchartElementGroupTab,
  eventSubTab: BpmnPaletteCategoryId
): BpmnPaletteCategoryId | null {
  if (group === "events") return eventSubTab;
  if (group === "lanes") return null;
  return group;
}

export { BPMN_PALETTE_CATEGORIES, paletteByCategory };

export type DiagramEditorAction = {
  id: string;
  label: string;
  icon: LucideIcon;
  hint: string;
};

export function createDiagramEditorActions(labels: FlowchartEditorLabels): DiagramEditorAction[] {
  return [
    { id: "addLane", label: labels.editorActions.find((a) => a.id === "addLane")?.label ?? "Lane", icon: Plus, hint: labels.addLane },
    { id: "autoLayout", label: labels.editorActions.find((a) => a.id === "autoLayout")?.label ?? "Auto layout", icon: Wand2, hint: labels.autoLayout },
    { id: "templateLinear", label: labels.editorActions.find((a) => a.id === "templateLinear")?.label ?? "Linear", icon: Rows3, hint: labels.templateLinear },
    { id: "templateDecision", label: labels.editorActions.find((a) => a.id === "templateDecision")?.label ?? "Decision", icon: GitBranch, hint: labels.templateDecision },
    { id: "templateSwimlanes", label: labels.editorActions.find((a) => a.id === "templateSwimlanes")?.label ?? "Swimlanes", icon: Layers, hint: labels.templateSwimlanes },
  ];
}

export function createDiagramEditorSelectionActions(labels: FlowchartEditorLabels): DiagramEditorAction[] {
  const iconById: Record<string, LucideIcon> = {
    delete: Trash2,
    copy: Copy,
    paste: ClipboardPaste,
    duplicate: CopyPlus,
    cycleEdgeKind: GitCompareArrows,
  };
  return labels.selectionActions.map((action) => ({
    ...action,
    icon: iconById[action.id] ?? Trash2,
  }));
}

export function diagramEditorAddLaneAction(labels: FlowchartEditorLabels) {
  return createDiagramEditorActions(labels)[0];
}

export function diagramEditorLayoutActions(labels: FlowchartEditorLabels) {
  return createDiagramEditorActions(labels).slice(1);
}
