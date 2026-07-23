import { describe, expect, it } from "vitest";

import { toggleContentRunStyleInRange } from "./comunicadoContentRunEditing";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";

describe("toggleContentRunStyleInRange — só o trecho selecionado", () => {
  it("negrito em «negrito» não marca «Texto teste »", () => {
    const text = "Texto teste negrito";
    const start = text.indexOf("negrito");
    const end = text.length;
    const next = toggleContentRunStyleInRange([{ text }], start, end, "fontWeight");
    expect(plainTextFromContentRuns(next)).toBe(text);
    expect(next.length).toBeGreaterThanOrEqual(2);
    const boldParts = next.filter((run) => run.style?.fontWeight === "bold");
    const plainParts = next.filter((run) => run.style?.fontWeight !== "bold");
    expect(boldParts.map((run) => run.text).join("")).toBe("negrito");
    expect(plainParts.map((run) => run.text).join("")).toBe("Texto teste ");
  });
});
