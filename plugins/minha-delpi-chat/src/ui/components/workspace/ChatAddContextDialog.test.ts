import { describe, expect, it } from "vitest";

import { isPinnableContextKind, isUserContextItemKind } from "../../chatActiveContext";

describe("context chip kinds", () => {
  it("identifica tipos fixáveis operacionais", () => {
    expect(isPinnableContextKind("context")).toBe(true);
    expect(isPinnableContextKind("branch")).toBe(true);
    expect(isPinnableContextKind("warehouse")).toBe(true);
    expect(isPinnableContextKind("tone")).toBe(false);
  });

  it("identifica itens de contexto livre", () => {
    expect(isUserContextItemKind("note")).toBe(true);
    expect(isUserContextItemKind("table")).toBe(true);
    expect(isUserContextItemKind("question")).toBe(true);
    expect(isUserContextItemKind("answer")).toBe(true);
    expect(isUserContextItemKind("context")).toBe(true);
    expect(isUserContextItemKind("product")).toBe(false);
  });
});
