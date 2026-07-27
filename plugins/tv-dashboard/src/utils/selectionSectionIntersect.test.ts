import { describe, expect, it } from "vitest";

import {
  aggregateEqualValues,
  filterMultiExcludedSections,
  intersectOrderedIds,
} from "./selectionSectionIntersect";

describe("selectionSectionIntersect", () => {
  it("aggregateEqualValues: igual → valor; divergente → mixed", () => {
    expect(aggregateEqualValues([12, 12, 12])).toBe(12);
    expect(aggregateEqualValues([12, 78])).toBe("mixed");
    expect(aggregateEqualValues([])).toBeUndefined();
  });

  it("intersectOrderedIds preserva ordem do primary", () => {
    expect(
      intersectOrderedIds([
        ["visualBox", "display", "organize", "actions"],
        ["media", "display", "organize", "actions"],
      ]),
    ).toEqual(["display", "organize", "actions"]);
  });

  it("filterMultiExcludedSections remove frame/animation", () => {
    expect(
      filterMultiExcludedSections(
        ["visualBox", "frame", "animation", "organize"],
        new Set(["frame", "animation"]),
      ),
    ).toEqual(["visualBox", "organize"]);
  });
});
