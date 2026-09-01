import { describe, expect, it } from "vitest";

import {
  canUnmergeCanvasTableSelection,
  resolveCanvasTableMergeCommand,
  resolveCanvasTableMergeShortcut,
} from "./canvasTableMergeCommands";

const MERGE_2X2 = { row: 0, col: 0, rowspan: 2, colspan: 2 };
const CELLS_2X2 = [
  { row: 0, col: 0 },
  { row: 0, col: 1 },
  { row: 1, col: 0 },
  { row: 1, col: 1 },
];

describe("canvasTableMergeCommands", () => {
  it("mescla retângulo ≥2 e rejeita célula única", () => {
    expect(
      resolveCanvasTableMergeCommand({ cells: CELLS_2X2, merges: [], mode: "merge" }),
    ).toEqual([MERGE_2X2]);
    expect(
      resolveCanvasTableMergeCommand({
        cells: [{ row: 0, col: 0 }],
        merges: [],
        mode: "merge",
      }),
    ).toBeNull();
  });

  it("desmescla quando a seleção cobre um merge", () => {
    expect(canUnmergeCanvasTableSelection([MERGE_2X2], [{ row: 1, col: 1 }])).toBe(true);
    expect(
      resolveCanvasTableMergeCommand({
        cells: [{ row: 0, col: 0 }],
        merges: [MERGE_2X2],
        mode: "unmerge",
      }),
    ).toEqual([]);
  });

  it("atalhos Ctrl+M / Ctrl+Shift+M", () => {
    expect(
      resolveCanvasTableMergeShortcut({ key: "m", ctrl: true, meta: false, shift: false }),
    ).toBe("merge");
    expect(
      resolveCanvasTableMergeShortcut({ key: "M", ctrl: true, meta: false, shift: true }),
    ).toBe("unmerge");
    expect(
      resolveCanvasTableMergeShortcut({ key: "m", ctrl: false, meta: false, shift: false }),
    ).toBeNull();
  });
});
