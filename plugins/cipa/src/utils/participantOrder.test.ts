import { describe, expect, it } from "vitest";

import { moveArrayItemAt, participantsWithSortOrder } from "./participantOrder";

describe("participantOrder", () => {
  it("moveArrayItemAt troca posições adjacentes", () => {
    expect(moveArrayItemAt(["a", "b", "c"], 0, 1)).toEqual(["b", "a", "c"]);
    expect(moveArrayItemAt(["a", "b", "c"], 2, -1)).toEqual(["a", "c", "b"]);
  });

  it("moveArrayItemAt ignora movimento fora dos limites", () => {
    const items = ["a", "b"];
    expect(moveArrayItemAt(items, 0, -1)).toBe(items);
    expect(moveArrayItemAt(items, 1, 1)).toBe(items);
  });

  it("participantsWithSortOrder grava sort_order sequencial", () => {
    expect(
      participantsWithSortOrder([
        { display_name: "Ana" },
        { display_name: "Bob" },
      ]),
    ).toEqual([
      { display_name: "Ana", sort_order: 0 },
      { display_name: "Bob", sort_order: 1 },
    ]);
  });
});
