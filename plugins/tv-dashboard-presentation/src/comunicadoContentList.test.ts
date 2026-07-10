import { describe, expect, it } from "vitest";

import {
  groupContentRunsForDisplay,
  hasListContentRuns,
  insertLineBreakAtOffset,
  joinContentLinesToRuns,
  selectionListTypeState,
  splitContentRunsIntoLines,
  toggleListTypeInRange,
  toggleListTypeOnAllLines,
} from "./comunicadoContentList";
import { syncTextBlockFromRuns } from "./comunicadoContentRunEditing";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("comunicadoContentList", () => {
  it("divide runs em linhas e preserva listType", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "Um", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Dois", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Três", style: { listType: "bullet" } },
    ];
    expect(splitContentRunsIntoLines(runs)).toEqual([
      { runs: [{ text: "Um", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "Dois", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "Três", style: { listType: "bullet" } }], listType: "bullet" },
    ]);
  });

  it("aplica marcadores só nas linhas selecionadas", () => {
    const runs: ComunicadoContentRun[] = [{ text: "A\nB\nC" }];
    const toggled = toggleListTypeInRange(runs, 2, 4, "bullet");
    expect(splitContentRunsIntoLines(toggled)).toEqual([
      { runs: [{ text: "A" }] },
      { runs: [{ text: "B", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "C" }] },
    ]);
  });

  it("remove marcadores quando toda a linha já usa o mesmo tipo", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "Item", style: { listType: "ordered" } },
      { text: "\n" },
      { text: "Dois", style: { listType: "ordered" } },
    ];
    const toggled = toggleListTypeInRange(runs, 0, 10, "ordered");
    expect(hasListContentRuns(toggled)).toBe(false);
  });

  it("agrupa linhas consecutivas para renderização na TV", () => {
    const runs: ComunicadoContentRun[] = joinContentLinesToRuns([
      { runs: [{ text: "Intro" }] },
      { runs: [{ text: "A", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "B", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "C", style: { listType: "bullet" } }], listType: "bullet" },
    ]);
    expect(groupContentRunsForDisplay(runs)).toEqual([
      { kind: "text", runs: [{ text: "Intro" }] },
      {
        kind: "list",
        listType: "bullet",
        items: [
          [{ text: "A", style: { listType: "bullet" } }],
          [{ text: "B", style: { listType: "bullet" } }],
          [{ text: "C", style: { listType: "bullet" } }],
        ],
      },
    ]);
  });

  it("persiste contentRuns com listType", () => {
    const synced = syncTextBlockFromRuns(
      toggleListTypeOnAllLines([{ text: "A\nB\nC" }], "bullet"),
    );
    expect(synced.content).toBe("A\nB\nC");
    expect(synced.contentRuns?.some((run) => run.style?.listType === "bullet")).toBe(true);
  });

  it("insere quebra de linha herdando listType", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "AB", style: { listType: "bullet" } },
    ];
    const next = insertLineBreakAtOffset(runs, 1);
    expect(splitContentRunsIntoLines(next)).toEqual([
      { runs: [{ text: "A", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "B", style: { listType: "bullet" } }], listType: "bullet" },
    ]);
  });

  it("detecta estado de seleção misto", () => {
    const runs: ComunicadoContentRun[] = joinContentLinesToRuns([
      { runs: [{ text: "A", style: { listType: "bullet" } }], listType: "bullet" },
      { runs: [{ text: "B" }] },
    ]);
    expect(selectionListTypeState(runs, 0, 3)).toEqual({
      bullet: "mixed",
      ordered: false,
    });
  });
});
