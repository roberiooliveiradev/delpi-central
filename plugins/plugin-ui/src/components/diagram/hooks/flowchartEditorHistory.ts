import type { FlowchartV1 } from "../types/diagram";

export const FLOWCHART_EDITOR_HISTORY_LIMIT = 50;

export function cloneFlowchartSnapshot(value: FlowchartV1): FlowchartV1 {
  return structuredClone(value);
}

export type FlowchartHistoryStacks = {
  past: FlowchartV1[];
  future: FlowchartV1[];
};

export function emptyFlowchartHistory(): FlowchartHistoryStacks {
  return { past: [], future: [] };
}

/** Empilha snapshot atual e limpa o future (novo ramo de edição). */
export function pushFlowchartHistoryPast(
  stacks: FlowchartHistoryStacks,
  snapshot: FlowchartV1,
  limit = FLOWCHART_EDITOR_HISTORY_LIMIT,
): FlowchartHistoryStacks {
  return {
    past: [...stacks.past.slice(-(limit - 1)), cloneFlowchartSnapshot(snapshot)],
    future: [],
  };
}

export function undoFlowchartHistory(
  stacks: FlowchartHistoryStacks,
  current: FlowchartV1,
): { stacks: FlowchartHistoryStacks; next: FlowchartV1 } | null {
  if (!stacks.past.length) return null;
  const past = [...stacks.past];
  const previous = past.pop()!;
  return {
    stacks: {
      past,
      future: [...stacks.future, cloneFlowchartSnapshot(current)],
    },
    next: cloneFlowchartSnapshot(previous),
  };
}

export function redoFlowchartHistory(
  stacks: FlowchartHistoryStacks,
  current: FlowchartV1,
): { stacks: FlowchartHistoryStacks; next: FlowchartV1 } | null {
  if (!stacks.future.length) return null;
  const future = [...stacks.future];
  const restored = future.pop()!;
  return {
    stacks: {
      past: [...stacks.past, cloneFlowchartSnapshot(current)],
      future,
    },
    next: cloneFlowchartSnapshot(restored),
  };
}
