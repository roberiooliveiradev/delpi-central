import { describe, expect, it } from "vitest";

import { moveArrayItem } from "../hooks/useProjectionDragReorder";

describe("moveArrayItem", () => {
  it("move item para frente e para trás", () => {
    expect(moveArrayItem(["a", "b", "c"], 0, 2)).toEqual(["b", "c", "a"]);
    expect(moveArrayItem(["a", "b", "c"], 2, 0)).toEqual(["c", "a", "b"]);
  });

  it("ignora índices inválidos", () => {
    expect(moveArrayItem(["a", "b"], 0, 0)).toEqual(["a", "b"]);
    expect(moveArrayItem(["a", "b"], -1, 1)).toEqual(["a", "b"]);
  });
});
