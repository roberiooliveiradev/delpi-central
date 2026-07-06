import {
  Circle,
  CircleDot,
  Database,
  Diamond,
  FileText,
  GitBranch,
  LayoutGrid,
  Layers,
  MessageSquare,
  Plus,
  Rows3,
  Square,
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
    label: "+ Faixa (swimlane)",
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
