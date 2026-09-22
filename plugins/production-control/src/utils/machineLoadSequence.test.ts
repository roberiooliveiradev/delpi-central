import { describe, expect, it } from "vitest";

import { moveArrayItem } from "../hooks/useMachineLoadRowReorder";
import {
  applyKeyOrder,
  keysFromOperations,
  type SequenceKey,
} from "../hooks/useMachineLoadSequenceHistory";
import { mergeActiveOrderIntoMachineLoadQueue } from "./machineLoadVisibleReorder";

describe("moveArrayItem", () => {
  it("moves an item forward", () => {
    expect(moveArrayItem(["a", "b", "c"], 0, 2)).toEqual(["b", "c", "a"]);
  });

  it("moves an item backward", () => {
    expect(moveArrayItem(["a", "b", "c"], 2, 0)).toEqual(["c", "a", "b"]);
  });

  it("returns the same array reference when indexes are equal", () => {
    const items = ["a", "b"];
    expect(moveArrayItem(items, 1, 1)).toBe(items);
  });
});

describe("keysFromOperations", () => {
  it("maps production order + operation code", () => {
    expect(
      keysFromOperations([
        { production_order: "1", operation_code: "01" },
        { production_order: "2", operation_code: "02" },
      ]),
    ).toEqual([
      { production_order: "1", operation_code: "01" },
      { production_order: "2", operation_code: "02" },
    ]);
  });
});

describe("applyKeyOrder", () => {
  const rows = [
    { production_order: "A", operation_code: "01", label: "first" },
    { production_order: "B", operation_code: "01", label: "second" },
    { production_order: "C", operation_code: "01", label: "third" },
  ];

  it("reorders rows to match the key sequence", () => {
    const keys: SequenceKey[] = [
      { production_order: "C", operation_code: "01" },
      { production_order: "A", operation_code: "01" },
      { production_order: "B", operation_code: "01" },
    ];
    expect(applyKeyOrder(rows, keys).map((row) => row.label)).toEqual([
      "third",
      "first",
      "second",
    ]);
  });

  it("keeps the original order when keys are incomplete", () => {
    const keys: SequenceKey[] = [{ production_order: "A", operation_code: "01" }];
    expect(applyKeyOrder(rows, keys)).toBe(rows);
  });
});

describe("undo stack semantics", () => {
  it("pushes previous order and restores LIFO", () => {
    const stack: SequenceKey[][] = [];
    const push = (previous: SequenceKey[]) => {
      stack.push(previous);
      if (stack.length > 50) stack.shift();
    };
    const undo = (): SequenceKey[] | null => stack.pop() ?? null;

    const initial = keysFromOperations(rowsFixture());
    const afterDrop = [
      { production_order: "C", operation_code: "01" },
      { production_order: "A", operation_code: "01" },
      { production_order: "B", operation_code: "01" },
    ];
    push(initial);
    expect(undo()).toEqual(initial);
    expect(undo()).toBeNull();
    push(initial);
    push(afterDrop);
    expect(undo()).toEqual(afterDrop);
    expect(undo()).toEqual(initial);
  });
});

function rowsFixture() {
  return [
    { production_order: "A", operation_code: "01" },
    { production_order: "B", operation_code: "01" },
    { production_order: "C", operation_code: "01" },
  ];
}

describe("mergeActiveOrderIntoMachineLoadQueue", () => {
  const full = [
    {
      production_order: "F1",
      operation_code: "01",
      operation_pending_qty: 0,
      label: "finished-top",
    },
    {
      production_order: "A",
      operation_code: "01",
      operation_pending_qty: 10,
      label: "active-a",
    },
    {
      production_order: "F2",
      operation_code: "01",
      operation_pending_qty: 0,
      label: "finished-mid",
    },
    {
      production_order: "B",
      operation_code: "01",
      operation_pending_qty: 5,
      label: "active-b",
    },
    {
      production_order: "C",
      operation_code: "01",
      operation_pending_qty: 3,
      label: "active-c",
    },
  ];

  it("reorders only active slots and pins finished positions (positive)", () => {
    const reorderedActive = [full[4]!, full[1]!, full[3]!];
    expect(mergeActiveOrderIntoMachineLoadQueue(full, reorderedActive).map((row) => row.label)).toEqual([
      "finished-top",
      "active-c",
      "finished-mid",
      "active-a",
      "active-b",
    ]);
  });

  it("returns the visible list unchanged when it is already the full queue (sibling)", () => {
    const onlyActive = full.filter((row) => (row.operation_pending_qty ?? 0) > 0);
    const reordered = [onlyActive[1]!, onlyActive[0]!, onlyActive[2]!];
    expect(mergeActiveOrderIntoMachineLoadQueue(onlyActive, reordered).map((row) => row.label)).toEqual([
      "active-b",
      "active-a",
      "active-c",
    ]);
  });

  it("keeps the full queue when the active set does not match (negative)", () => {
    const incomplete = [full[1]!, full[3]!];
    expect(mergeActiveOrderIntoMachineLoadQueue(full, incomplete)).toBe(full);
  });
});
