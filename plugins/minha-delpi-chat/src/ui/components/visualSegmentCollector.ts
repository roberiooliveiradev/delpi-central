import type { ChatPresentation, ChatToolCall } from "../../data/api/chatTypes";
import type { AssistantContentSegment } from "./assistantContentTypes";
import { normalizeChartPresentation } from "./chartPresentationNormalize";
import { shouldSkipTableSegment } from "./presentationStructureDedup";
import {
  dedupeTablePresentations,
  dedupeTableSegments,
} from "./presentationTableDedup";
import { shouldRenderDashboardSegment } from "./chatPresentation";
import { getStackPresentationPlanFromToolCalls } from "./presentationStackPlan";
import { appendVisualSegment } from "./segmentDedupe";

function isSuppressedToolCall(toolCall: ChatToolCall): boolean {
  const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;

  if (metadata.sqlSchemaPrefetch === true || metadata.suppressClientPresentation === true) {
    return true;
  }

  const path = String(metadata.path || "").toLowerCase();

  return (
    path.includes("/system/tables") &&
    (path.includes("/columns") || path.includes("/schema") || path.includes("/relations"))
  );
}

export function collectVisualSegments(toolCalls: ChatToolCall[]): AssistantContentSegment[] {
  const segments: AssistantContentSegment[] = [];
  const tableCandidates: Extract<ChatPresentation, { type: "table" }>[] = [];
  const stackPlan = getStackPresentationPlanFromToolCalls(toolCalls);
  const allowDashboard = shouldRenderDashboardSegment(toolCalls, stackPlan.tailVisualOrder);

  const queueTable = (presentation: Extract<ChatPresentation, { type: "table" }>) => {
    if (shouldSkipTableSegment(presentation, toolCalls)) {
      return;
    }

    tableCandidates.push(presentation);
  };

  for (const toolCall of toolCalls) {
    if (toolCall.name && toolCall.name !== "execute_external_action") {
      continue;
    }

    if (isSuppressedToolCall(toolCall)) {
      continue;
    }

    const metadata = (toolCall.metadata ?? {}) as Record<string, unknown>;
    const presentation = metadata.presentation;

    if (presentation && typeof presentation === "object" && "type" in presentation) {
      const typed = presentation as ChatPresentation;

      if (typed.type === "table") {
        queueTable(typed);
      } else if (typed.type === "chart") {
        appendVisualSegment(segments, { kind: "chart", presentation: typed });
      } else if (typed.type === "tree") {
        appendVisualSegment(segments, { kind: "tree", presentation: typed });
      } else if (typed.type === "kpi") {
        appendVisualSegment(segments, { kind: "kpi", presentation: typed });
      } else if (typed.type === "dashboard" && allowDashboard) {
        appendVisualSegment(segments, { kind: "dashboard", presentation: typed });
      }
    }

    const bundledTables = metadata.tablePresentations;

    if (Array.isArray(bundledTables) && bundledTables.length) {
      for (const candidate of bundledTables) {
        if (
          candidate &&
          typeof candidate === "object" &&
          (candidate as ChatPresentation).type === "table"
        ) {
          queueTable(candidate as Extract<ChatPresentation, { type: "table" }>);
        }
      }
    } else {
      for (const key of [
        "tablePresentation",
        "profileTablePresentation",
        "inspectionTablePresentation",
      ]) {
        const slot = metadata[key];

        if (
          slot &&
          typeof slot === "object" &&
          (slot as ChatPresentation).type === "table"
        ) {
          queueTable(slot as Extract<ChatPresentation, { type: "table" }>);
        }
      }
    }

    const chartPresentation = normalizeChartPresentation(metadata.chartPresentation);

    if (chartPresentation) {
      appendVisualSegment(segments, {
        kind: "chart",
        presentation: chartPresentation,
      });
    }

    const treePresentation = metadata.treePresentation;

    if (
      treePresentation &&
      typeof treePresentation === "object" &&
      (treePresentation as ChatPresentation).type === "tree"
    ) {
      appendVisualSegment(segments, {
        kind: "tree",
        presentation: treePresentation as Extract<ChatPresentation, { type: "tree" }>,
      });
    }

    const kpiPresentation = metadata.kpiPresentation;

    if (
      kpiPresentation &&
      typeof kpiPresentation === "object" &&
      (kpiPresentation as ChatPresentation).type === "kpi"
    ) {
      appendVisualSegment(segments, {
        kind: "kpi",
        presentation: kpiPresentation as Extract<ChatPresentation, { type: "kpi" }>,
      });
    }

    const dashboardPresentation = metadata.dashboardPresentation;

    if (
      allowDashboard &&
      dashboardPresentation &&
      typeof dashboardPresentation === "object" &&
      (dashboardPresentation as ChatPresentation).type === "dashboard"
    ) {
      appendVisualSegment(segments, {
        kind: "dashboard",
        presentation: dashboardPresentation as Extract<ChatPresentation, { type: "dashboard" }>,
      });
    }
  }

  for (const table of dedupeTablePresentations(tableCandidates)) {
    appendVisualSegment(segments, { kind: "table", presentation: table });
  }

  return dedupeTableSegments(segments);
}
