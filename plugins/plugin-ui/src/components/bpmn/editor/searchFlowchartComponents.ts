import type { LucideIcon } from "lucide-react";

import {
  searchBpmnPalette,
  type FlowchartNodeType,
} from "../model/bpmnNodeCatalog";
import type { FlowchartEditorLabels } from "../model/flowchartEditorLabels";
import {
  createDiagramEditorActions,
  flowchartElementGroupTabs,
  type DiagramEditorAction,
} from "./flowchartEditorToolbar";

export type FlowchartComponentSearchHit =
  | {
      kind: "node";
      id: string;
      type: FlowchartNodeType;
      label: string;
      categoryLabel: string;
      hint: string;
    }
  | {
      kind: "action";
      id: string;
      actionId: DiagramEditorAction["id"];
      label: string;
      categoryLabel: string;
      hint: string;
      icon: LucideIcon;
    };

function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim();
}

function scoreLabelMatch(label: string, needle: string): number {
  const labelNorm = normalizeSearchText(label);
  if (labelNorm === needle) return 0;
  if (labelNorm.startsWith(needle)) return 1;
  if (labelNorm.includes(needle)) return 2;
  return 3;
}

function scoreHaystack(parts: string[], needle: string, label: string): number | null {
  const haystack = normalizeSearchText(parts.join(" "));
  if (!haystack.includes(needle)) return null;
  return scoreLabelMatch(label, needle);
}

const ACTION_EXTRA_KEYWORDS: Partial<Record<DiagramEditorAction["id"], string[]>> = {
  addLane: ["faixa", "faixas", "lane", "lanes", "swimlane", "swimlanes", "pista", "pistas"],
  autoLayout: ["layout", "organizar", "auto"],
  templateLinear: ["modelo", "template", "linear"],
  templateDecision: ["modelo", "template", "decisao", "decision"],
  templateSwimlanes: ["modelo", "template", "faixas", "swimlane", "swimlanes"],
};

/**
 * Busca unificada: nós da paleta BPMN + ações da ribbon (Faixa, modelos, layout).
 */
export function searchFlowchartComponents(
  query: string,
  labels: FlowchartEditorLabels,
  limit = 32,
): FlowchartComponentSearchHit[] {
  const needle = normalizeSearchText(query);
  if (!needle) return [];

  const scored: Array<FlowchartComponentSearchHit & { score: number }> = [];

  for (const hit of searchBpmnPalette(query, limit)) {
    const labelNorm = normalizeSearchText(hit.label);
    let score = 3;
    if (labelNorm === needle) score = 0;
    else if (labelNorm.startsWith(needle)) score = 1;
    else if (labelNorm.includes(needle)) score = 2;
    scored.push({
      kind: "node",
      id: `node:${hit.type}`,
      type: hit.type,
      label: hit.label,
      categoryLabel: hit.categoryLabel,
      hint: hit.hint,
      score,
    });
  }

  const groupTabs = flowchartElementGroupTabs(labels);
  const lanesGroupLabel =
    groupTabs.find((tab) => tab.id === "lanes")?.label ?? "Faixas";
  const modelsGroupLabel = labels.toolbarModelsTab;

  for (const action of createDiagramEditorActions(labels)) {
    const categoryLabel = action.id === "addLane" ? lanesGroupLabel : modelsGroupLabel;
    const extras = ACTION_EXTRA_KEYWORDS[action.id] ?? [];
    const score = scoreHaystack(
      [action.label, action.hint, categoryLabel, action.id, ...extras],
      needle,
      action.label,
    );
    if (score == null) continue;
    scored.push({
      kind: "action",
      id: `action:${action.id}`,
      actionId: action.id,
      label: action.label,
      categoryLabel,
      hint: action.hint,
      icon: action.icon,
      score,
    });
  }

  scored.sort(
    (a, b) => a.score - b.score || a.label.localeCompare(b.label, "pt-BR"),
  );
  return scored.slice(0, limit).map(({ score: _score, ...hit }) => hit);
}
