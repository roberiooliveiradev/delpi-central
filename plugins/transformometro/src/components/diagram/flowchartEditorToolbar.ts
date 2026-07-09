import {
  Circle,
  CircleDot,
  Copy,
  CopyPlus,
  Database,
  Diamond,
  FileText,
  GitBranch,
  LayoutGrid,
  Layers,
  MessageSquare,
  Move,
  Plus,
  Rows3,
  Square,
  Trash2,
  Wand2,
  type LucideIcon,
} from "lucide-react";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { FlowchartNodeType } from "../../types/diagram";

const D = TM_HELP_TOOLTIPS.diagramEditor;

export const FLOWCHART_NODE_ICONS: Record<FlowchartNodeType, LucideIcon> = {
  start: CircleDot,
  process: Square,
  decision: Diamond,
  document: FileText,
  data: Database,
  subprocess: Layers,
  end: Circle,
  comment: MessageSquare,
};

export function flowchartNodeHint(type: FlowchartNodeType): string {
  return D.nodes[type];
}

export const DIAGRAM_EDITOR_ACTIONS = [
  {
    id: "addLane",
    label: "Faixa (swimlane)",
    icon: Plus,
    hint: D.addLane,
  },
  {
    id: "autoLayout",
    label: "Auto-layout",
    icon: Wand2,
    hint: D.autoLayout,
  },
  {
    id: "templateLinear",
    label: "Template linear",
    icon: LayoutGrid,
    hint: D.templateLinear,
  },
  {
    id: "templateDecision",
    label: "Template com decisão",
    icon: GitBranch,
    hint: D.templateDecision,
  },
  {
    id: "templateSwimlanes",
    label: "Template BPMN + swimlanes",
    icon: Rows3,
    hint: D.templateSwimlanes,
  },
] as const;

export const DIAGRAM_EDITOR_LAYOUT_ACTIONS = DIAGRAM_EDITOR_ACTIONS.filter(
  (action) => action.id !== "addLane"
);

export const DIAGRAM_EDITOR_ADD_LANE_ACTION = DIAGRAM_EDITOR_ACTIONS.find(
  (action) => action.id === "addLane"
)!;

export const DIAGRAM_EDITOR_SELECTION_ACTIONS = [
  {
    id: "delete",
    label: "Excluir",
    icon: Trash2,
    hint: D.selectionDelete,
  },
  {
    id: "move",
    label: "Mover",
    icon: Move,
    hint: D.selectionMove,
  },
  {
    id: "copy",
    label: "Copiar",
    icon: Copy,
    hint: D.selectionCopy,
  },
  {
    id: "duplicate",
    label: "Duplicar",
    icon: CopyPlus,
    hint: D.selectionDuplicate,
  },
] as const;
