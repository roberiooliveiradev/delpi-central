import { describe, expect, it } from "vitest";

import { assignDomRef } from "./assignDomRef";

describe("assignDomRef", () => {
  it("monta, atualiza e desmonta um ref de objeto", () => {
    const ref: { current: HTMLElement | null } = { current: null };
    const assign = assignDomRef(ref);
    const first = document.createElement("div");
    const second = document.createElement("section");

    assign(first);
    expect(ref.current).toBe(first);
    assign(second);
    expect(ref.current).toBe(second);
    assign(null);
    expect(ref.current).toBeNull();
  });

  it("encaminha o nó para ref de função e ignora ref ausente", () => {
    const seen: Array<HTMLElement | null> = [];
    const assign = assignDomRef<HTMLElement>((node) => {
      seen.push(node);
    });
    const node = document.createElement("div");
    assign(node);
    assign(null);
    expect(seen).toEqual([node, null]);
    expect(() => assignDomRef(undefined)(node)).not.toThrow();
  });
});
