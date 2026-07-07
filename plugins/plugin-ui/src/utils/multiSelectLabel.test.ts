import { describe, expect, it } from "vitest";

import { buildMultiSelectTriggerLabel } from "./multiSelectLabel";

describe("buildMultiSelectTriggerLabel", () => {
  const options = [
    { value: "a", label: "Alpha" },
    { value: "b", label: "Beta" },
  ];

  it("retorna emptyLabel sem seleção", () => {
    expect(
      buildMultiSelectTriggerLabel([], options, "Todos", (count) => `${count} selecionado(s)`),
    ).toBe("Todos");
  });

  it("retorna label único com uma seleção", () => {
    expect(
      buildMultiSelectTriggerLabel(["a"], options, "Todos", (count) => `${count} selecionado(s)`),
    ).toBe("Alpha");
  });

  it("retorna contagem com múltiplas seleções", () => {
    expect(
      buildMultiSelectTriggerLabel(["a", "b"], options, "Todos", (count) => `${count} selecionado(s)`),
    ).toBe("2 selecionado(s)");
  });
});
