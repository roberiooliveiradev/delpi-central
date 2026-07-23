import { describe, expect, it } from "vitest";

import {
  expandRangeToDataRefAtoms,
  toggleContentRunStyleInRange,
} from "./comunicadoContentRunEditing";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("formatação em campo dinâmico (dataRef)", () => {
  const runs: ComunicadoContentRun[] = [
    { text: "Meta " },
    { text: "1.400", dataRef: { field: "ppm", format: "number", label: "ppm" } },
    { text: " PPM" },
  ];

  it("expande seleção parcial do valor dinâmico para o run atômico", () => {
    const start = "Meta ".length + 2;
    const end = "Meta ".length + 4;
    expect(expandRangeToDataRefAtoms(runs, start, end)).toEqual({
      start: "Meta ".length,
      end: "Meta ".length + "1.400".length,
    });
  });

  it("negrito no campo dinâmico não marca o container e preserva dataRef", () => {
    const start = "Meta ".length;
    const end = start + "1.400".length;
    const next = toggleContentRunStyleInRange(runs, start, end, "fontWeight");
    expect(plainTextFromContentRuns(next)).toBe("Meta 1.400 PPM");
    const dynamic = next.find((run) => run.dataRef?.field === "ppm");
    expect(dynamic?.style?.fontWeight).toBe("bold");
    expect(dynamic?.text).toBe("1.400");
    expect(next.find((run) => run.text === "Meta ")?.style?.fontWeight).not.toBe("bold");
    expect(next.find((run) => run.text === " PPM")?.style?.fontWeight).not.toBe("bold");
  });
});
