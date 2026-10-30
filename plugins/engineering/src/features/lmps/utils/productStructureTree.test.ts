import { describe, expect, it } from "vitest";

import {
  buildProductStructureTree,
  countRichTreeNodes,
} from "./productStructureTree";

describe("buildProductStructureTree", () => {
  it("maps root + nested components preserving code/qty/unit/type", () => {
    const root = buildProductStructureTree({
      root: { code: "90000001", description: "PAI", type: "PA", quantity: 1 },
      items: [
        {
          code: "80000001",
          description: "INTERMEDIARIO",
          type: "PI",
          quantity: 2,
          unit: "PC",
          components: [
            {
              code: "10000001",
              description: "MP",
              type: "MP",
              quantity: 3,
              unit: "KG",
            },
          ],
        },
      ],
    });

    expect(root).not.toBeNull();
    expect(root!.label).toBe("90000001");
    expect(root!.navCode).toBe("90000001");
    expect(root!.children).toHaveLength(1);
    const child = root!.children![0];
    expect(child.label).toBe("80000001");
    expect(child.badge).toBe("PI");
    expect(child.metaCaption).toContain("2");
    expect(child.children![0].label).toBe("10000001");
    expect(countRichTreeNodes(root!)).toBe(3);
  });

  it("uses `parents` as child key for where-used payloads", () => {
    const root = buildProductStructureTree({
      items: [
        {
          code: "P1",
          description: "PAI",
          parents: [{ code: "GP1", description: "AVO" }],
        },
      ],
    });

    expect(root).not.toBeNull();
    expect(root!.children![0].label).toBe("GP1");
    expect(root!.children![0].navCode).toBe("GP1");
  });

  it("omits navCode on synthetic root and placeholder codes", () => {
    const root = buildProductStructureTree({
      items: [{ code: "A" }, { code: "B" }],
    });

    expect(root).not.toBeNull();
    expect(root!.navCode).toBeUndefined();
    expect(root!.children).toHaveLength(2);
  });

  it("returns null for empty/missing payloads", () => {
    expect(buildProductStructureTree(null)).toBeNull();
    expect(buildProductStructureTree({ items: [] })).toBeNull();
  });
});
