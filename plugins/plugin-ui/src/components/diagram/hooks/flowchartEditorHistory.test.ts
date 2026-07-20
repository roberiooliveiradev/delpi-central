import { describe, expect, it } from "vitest";

import type { FlowchartV1 } from "../types/diagram";
import {
  cloneFlowchartSnapshot,
  emptyFlowchartHistory,
  FLOWCHART_EDITOR_HISTORY_LIMIT,
  pushFlowchartHistoryPast,
  redoFlowchartHistory,
  undoFlowchartHistory,
} from "./flowchartEditorHistory";

function flow(partial: Partial<FlowchartV1> & { nodes: FlowchartV1["nodes"] }): FlowchartV1 {
  return {
    format: "flowchart_v1",
    format_version: 1,
    edges: [],
    ...partial,
  };
}

describe("flowchartEditorHistory", () => {
  it("empilha past e limpa future no push", () => {
    const a = flow({ nodes: [{ id: "a", type: "process", label: "A", position: { x: 0, y: 0 } }] });
    const b = flow({ nodes: [{ id: "b", type: "process", label: "B", position: { x: 0, y: 0 } }] });
    let stacks = pushFlowchartHistoryPast(emptyFlowchartHistory(), a);
    expect(stacks.past).toHaveLength(1);
    expect(stacks.future).toHaveLength(0);

    const undone = undoFlowchartHistory(stacks, b);
    expect(undone?.next.nodes[0]?.id).toBe("a");
    expect(undone?.stacks.future).toHaveLength(1);

    const redone = redoFlowchartHistory(undone!.stacks, a);
    expect(redone?.next.nodes[0]?.id).toBe("b");
  });

  it("cloneFlowchartSnapshot isola mutações", () => {
    const original = flow({
      nodes: [{ id: "n1", type: "process", label: "X", position: { x: 1, y: 2 } }],
    });
    const cloned = cloneFlowchartSnapshot(original);
    cloned.nodes[0].label = "Y";
    expect(original.nodes[0].label).toBe("X");
  });

  it("respeita o limite da pilha", () => {
    let stacks = emptyFlowchartHistory();
    for (let i = 0; i < FLOWCHART_EDITOR_HISTORY_LIMIT + 10; i += 1) {
      stacks = pushFlowchartHistoryPast(
        stacks,
        flow({
          nodes: [
            {
              id: `n${i}`,
              type: "process",
              label: String(i),
              position: { x: 0, y: 0 },
            },
          ],
        }),
      );
    }
    expect(stacks.past).toHaveLength(FLOWCHART_EDITOR_HISTORY_LIMIT);
  });
});
