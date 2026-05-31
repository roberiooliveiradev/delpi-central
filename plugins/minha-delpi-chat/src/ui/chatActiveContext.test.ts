import { describe, expect, it } from "vitest";

import {
  collectActiveContextChips,
  contextChipKey,
  mergeContextChips,
} from "./chatActiveContext";

describe("chatActiveContext", () => {
  it("deduplica e ordena chips por tipo", () => {
    const merged = mergeContextChips([
      [
        { label: "Tom direto", kind: "tone", value: "direct" },
        { label: "Produto 10080001", kind: "product", value: "10080001" },
      ],
      [{ label: "Filial 02", kind: "branch", value: "02" }],
    ]);

    expect(merged.map((chip) => chip.kind)).toEqual(["product", "branch", "tone"]);
  });

  it("agrega chips de várias mensagens do assistente", () => {
    const chips = collectActiveContextChips([
      { role: "user", metadata: {} },
      {
        role: "assistant",
        metadata: {
          contextChips: [{ label: "Produto 10080022", kind: "product", value: "10080022" }],
        },
      },
      {
        role: "assistant",
        metadata: {
          contextChips: [{ label: "Filial 02", kind: "branch", value: "02" }],
        },
      },
    ]);

    expect(chips).toHaveLength(2);
    expect(contextChipKey(chips[0])).toBe("product:10080022");
    expect(contextChipKey(chips[1])).toBe("branch:02");
  });
});
