import { describe, expect, it } from "vitest";

import { buildManualContextChip } from "./ChatAddContextDialog";
import { isPinnableContextKind } from "../chatActiveContext";

describe("ChatAddContextDialog", () => {
  it("monta chip de armazém", () => {
    expect(buildManualContextChip("warehouse", "01")).toEqual({
      kind: "warehouse",
      value: "01",
      label: "Armazém 01",
    });
  });

  it("rejeita produto inválido", () => {
    expect(buildManualContextChip("product", "abc")).toBeNull();
  });
});

describe("isPinnableContextKind", () => {
  it("identifica tipos fixáveis", () => {
    expect(isPinnableContextKind("branch")).toBe(true);
    expect(isPinnableContextKind("warehouse")).toBe(true);
    expect(isPinnableContextKind("tone")).toBe(false);
  });
});
