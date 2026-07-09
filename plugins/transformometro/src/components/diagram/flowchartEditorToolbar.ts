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

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  BPMN_NODE_DEFINITIONS,
  BPMN_PALETTE_CATEGORIES,
  paletteByCategory,
  type BpmnMarker,
  type BpmnPaletteCategoryId,
  type FlowchartNodeType,
} from "../../types/bpmnNodeCatalog";

const D = TM_HELP_TOOLTIPS.diagramEditor;

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

export function flowchartNodeHint(type: FlowchartNodeType): string {
  return BPMN_NODE_DEFINITIONS[type]?.hint ?? D.nodes.process;
}

export type FlowchartElementGroupTab =
  | "events"
  | "gateways"
  | "tasks"
  | "activities"
  | "artifacts"
  | "boundary"
  | "lanes";

export const FLOWCHART_ELEMENT_GROUP_TABS: Array<{ id: FlowchartElementGroupTab; label: string }> = [
  { id: "events", label: "Eventos" },
  { id: "gateways", label: "Desvios" },
  { id: "tasks", label: "Tarefas" },
  { id: "activities", label: "Atividades" },
  { id: "artifacts", label: "Artefatos" },
  { id: "boundary", label: "Borda" },
  { id: "lanes", label: "Faixas" },
];

export const FLOWCHART_EVENT_SUB_TABS: Array<{ id: BpmnPaletteCategoryId; label: string }> = [
  { id: "events_start", label: "Início" },
  { id: "events_intermediate", label: "Intermediários" },
  { id: "events_end", label: "Fim" },
];

export function resolvePaletteCategory(
  group: FlowchartElementGroupTab,
  eventSubTab: BpmnPaletteCategoryId
): BpmnPaletteCategoryId | null {
  if (group === "events") return eventSubTab;
  if (group === "lanes") return null;
  return group;
}

export { BPMN_PALETTE_CATEGORIES, paletteByCategory };

export const DIAGRAM_EDITOR_ACTIONS = [
  {
    id: "addLane",
    label: "Faixa",
    icon: Plus,
    hint: D.addLane,
  },
  {
    id: "autoLayout",
    label: "Layout automático",
    icon: Wand2,
    hint: D.autoLayout,
  },
  {
    id: "templateLinear",
    label: "Modelo linear",
    icon: Rows3,
    hint: D.templateLinear,
  },
  {
    id: "templateDecision",
    label: "Modelo decisão",
    icon: GitBranch,
    hint: D.templateDecision,
  },
  {
    id: "templateSwimlanes",
    label: "Modelo BPMN com faixas",
    icon: Layers,
    hint: D.templateSwimlanes,
  },
] as const;

export const DIAGRAM_EDITOR_ADD_LANE_ACTION = DIAGRAM_EDITOR_ACTIONS[0];
export const DIAGRAM_EDITOR_LAYOUT_ACTIONS = DIAGRAM_EDITOR_ACTIONS.slice(1);

export const DIAGRAM_EDITOR_SELECTION_ACTIONS = [
  { id: "delete", label: "Excluir", icon: Trash2, hint: D.selectionDelete },
  { id: "copy", label: "Copiar", icon: Copy, hint: D.selectionCopy },
  { id: "paste", label: "Colar", icon: ClipboardPaste, hint: D.selectionPaste },
  { id: "duplicate", label: "Duplicar", icon: CopyPlus, hint: D.selectionDuplicate },
  {
    id: "cycleEdgeKind",
    label: "Tipo de conexão",
    icon: GitCompareArrows,
    hint: D.selectionEdgeKind,
  },
] as const;
