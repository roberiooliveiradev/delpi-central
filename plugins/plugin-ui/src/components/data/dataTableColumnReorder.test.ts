import { describe, expect, it, vi } from "vitest";

import {
  applyTransparentColumnDragImage,
  reorderColumnKeys,
  reorderColumnKeysWithEdge,
  resolveColumnDropEdge,
} from "./dataTableColumnReorder";

describe("dataTableColumnReorder", () => {
  it("reorderColumnKeys move a chave para o índice do alvo", () => {
    expect(reorderColumnKeys(["a", "b", "c"], "c", "a")).toEqual(["c", "a", "b"]);
    expect(reorderColumnKeys(["a", "b", "c"], "a", "c")).toEqual(["b", "c", "a"]);
  });

  it("reorderColumnKeysWithEdge respeita before/after", () => {
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "c", "a", "before")).toEqual([
      "c",
      "a",
      "b",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "c", "a", "after")).toEqual([
      "a",
      "c",
      "b",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "a", "c", "before")).toEqual([
      "b",
      "a",
      "c",
    ]);
    expect(reorderColumnKeysWithEdge(["a", "b", "c"], "a", "c", "after")).toEqual([
      "b",
      "c",
      "a",
    ]);
  });

  it("resolveColumnDropEdge usa o centro do header", () => {
    const rect = { left: 100, width: 100 } as DOMRect;
    expect(resolveColumnDropEdge(120, rect)).toBe("before");
    expect(resolveColumnDropEdge(160, rect)).toBe("after");
    expect(resolveColumnDropEdge(10, { left: 0, width: 0 } as DOMRect)).toBe("before");
    expect(resolveColumnDropEdge(Number.NaN, rect)).toBe("before");
  });

  it("applyTransparentColumnDragImage usa canvas 1×1 (sem fantasma no DOM)", () => {
    const setDragImage = vi.fn();
    applyTransparentColumnDragImage({ setDragImage } as unknown as DataTransfer);
    expect(setDragImage).toHaveBeenCalledTimes(1);
    const image = setDragImage.mock.calls[0]?.[0] as HTMLCanvasElement;
    expect(image).toBeInstanceOf(HTMLCanvasElement);
    expect(image.width).toBe(1);
    expect(image.height).toBe(1);
    expect(document.querySelector(".delpi-ui-table__column-drag-ghost")).toBeNull();
  });
});
