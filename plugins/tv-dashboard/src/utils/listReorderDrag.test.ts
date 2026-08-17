import { describe, expect, it } from "vitest";

import { listDropHintClassName, resolveListDropEdge } from "./listReorderDrag";

describe("listReorderDrag", () => {
  const rect = { top: 100, height: 80 };

  it("metade superior é before; inferior é after", () => {
    expect(resolveListDropEdge(120, rect)).toBe("before");
    expect(resolveListDropEdge(139, rect)).toBe("before");
    expect(resolveListDropEdge(140, rect)).toBe("after");
    expect(resolveListDropEdge(170, rect)).toBe("after");
  });

  it("classe do indicador só no id alvo", () => {
    expect(listDropHintClassName({ id: "a", edge: "before" }, "a")).toBe("td-reorder--drop-before");
    expect(listDropHintClassName({ id: "a", edge: "after" }, "a")).toBe("td-reorder--drop-after");
    expect(listDropHintClassName({ id: "a", edge: "before" }, "b")).toBe("");
    expect(listDropHintClassName(null, "a")).toBe("");
  });
});
