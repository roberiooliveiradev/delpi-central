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
    expect(COMMON_RIBBON_TAIL).toEqual(["display", "organize", "actions"]);
    expect(COMMON_PANE_TAIL).toEqual([
      "display",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("withCommonTail full anexa animação e ações", () => {
    expect(withCommonTail(["typography", "shapeChrome"])).toEqual([
      "typography",
      "shapeChrome",
      "display",
      "organize",
      "animation",
      "actions",
    ]);
  });

  it("withCommonTail light só display+organize+actions", () => {
    expect(withCommonTail(["dataSourceHint"], "light")).toEqual([
      "dataSourceHint",
      "display",
      "organize",
      "actions",
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
