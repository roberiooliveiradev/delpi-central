import { describe, expect, it } from "vitest";

import {
  selectionRunStyleState,
  applyContentRunStyleInRange,
} from "./comunicadoContentRunEditing";
import {
  stripContentRunStylesOverriddenByContainer,
} from "./containerTypographyOverride";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("FORMAT-COMPOSITION-001 textCase selection + merge", () => {
  it("selectionRunStyleState agrega textCase e marca mixed", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "Aa", style: { textCase: "upper" } },
      { text: "Bb", style: { textCase: "lower" } },
    ];
    expect(selectionRunStyleState(runs, 0, 2).textCase).toBe("upper");
    expect(selectionRunStyleState(runs, 0, 4).textCase).toBe("mixed");
    expect(selectionRunStyleState(runs, 2, 4).textCase).toBe("lower");
  });

  it("applyContentRunStyleInRange textCase preserva dataRef + displayFormat", () => {
    const runs: ComunicadoContentRun[] = [
      {
        text: "…",
        dataRef: {
          field: "filter.end_date",
          displayFormat: { category: "date", formatId: "date-short" },
        },
        style: { fontWeight: "bold" },
      },
    ];
    const next = applyContentRunStyleInRange(runs, 0, 1, { textCase: "upper" });
    expect(next[0]?.dataRef?.field).toBe("filter.end_date");
    expect(next[0]?.dataRef?.displayFormat).toEqual({
      category: "date",
      formatId: "date-short",
    });
    expect(next[0]?.style?.textCase).toBe("upper");
    expect(next[0]?.style?.fontWeight).toBe("bold");
  });

  it("strip container fontWeight não apaga textCase do run (RQ-07)", () => {
    const runs: ComunicadoContentRun[] = [
      {
        text: "x",
        style: { fontWeight: "bold", textCase: "upper", color: "#111" },
        dataRef: {
          field: "filter.end_date",
          displayFormat: { category: "date", formatId: "date-short" },
        },
      },
    ];
    const next = stripContentRunStylesOverriddenByContainer(runs, ["fontWeight"]);
    expect(next?.[0]?.style?.fontWeight).toBeUndefined();
    expect(next?.[0]?.style?.textCase).toBe("upper");
    expect(next?.[0]?.style?.color).toBe("#111");
    expect(next?.[0]?.dataRef?.displayFormat).toEqual({
      category: "date",
      formatId: "date-short",
    });
  });
});
