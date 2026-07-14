import { describe, expect, it } from "vitest";

import {
  COMMON_PANE_TAIL,
  COMMON_RIBBON_TAIL,
  appendSectionIds,
  commonTailForLayout,
  withCommonTail,
} from "./commonSectionPresets";

describe("commonSectionPresets", () => {
  it("rabo ribbon vs pane", () => {
    expect(commonTailForLayout("ribbon")).toEqual([...COMMON_RIBBON_TAIL]);
    expect(commonTailForLayout("pane")).toEqual([...COMMON_PANE_TAIL]);
    expect(COMMON_RIBBON_TAIL).toEqual(["frame", "organize"]);
    expect(COMMON_PANE_TAIL).toEqual(["frame", "organize", "animation", "actions"]);
  });

  it("withCommonTail full anexa animação e ações", () => {
    expect(withCommonTail(["typography", "textBox"])).toEqual([
      "typography",
      "textBox",
      "frame",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("withCommonTail light só frame+organize", () => {
    expect(withCommonTail(["dataSourceHint"], "light")).toEqual([
      "dataSourceHint",
      "frame",
      "organize",
    ]);
  });

  it("appendSectionIds deduplica", () => {
    expect(appendSectionIds(["frame", "organize"], ["organize", "actions"])).toEqual([
      "frame",
      "organize",
      "actions",
    ]);
  });
});
