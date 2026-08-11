import { describe, expect, it } from "vitest";

import {
  promoteSelectionPrimary,
  resolveSelectionPrimaryId,
  resolveStageBlockSelection,
} from "./promoteSelectionPrimary";

describe("promoteSelectionPrimary", () => {
  it("move o clicado para o fim sem substituir a seleção", () => {
    expect(promoteSelectionPrimary(["a", "b", "c"], "a")).toEqual(["b", "c", "a"]);
    expect(promoteSelectionPrimary(["a", "b"], "b")).toEqual(["a", "b"]);
    expect(promoteSelectionPrimary(["a", "b"], "z")).toEqual(["a", "b"]);
  });

  it("resolve o primário como último id", () => {
    expect(resolveSelectionPrimaryId(["a", "b"])).toBe("b");
    expect(resolveStageBlockSelection({ selectedIds: ["x", "y"], clickedId: "x" })).toEqual([
      "y",
      "x",
    ]);
  });
});
