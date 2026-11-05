import { describe, expect, it } from "vitest";

import type { MyWegProbableDateShift } from "../types";
import {
  calendarDaysBetween,
  countProbableShiftKinds,
  filterProbableDateShifts,
  formatProductKeyForDisplay,
  normalizeProbableDateShifts,
  sortProbableDateShiftsByNearestRemessa,
} from "./mywegProbableDateShifts";

const sample: MyWegProbableDateShift[] = [
  {
    productKey: "code:80016354",
    fromRemessa: "2026-11-12",
    toRemessa: "2026-11-10",
    quantityUn: "2",
    kind: "possible_advancement",
    confidence: "probable_not_proven",
  },
  {
    productKey: "code:80016355",
    fromRemessa: "2026-11-08",
    toRemessa: "2026-11-13",
    quantityUn: "5.5",
    kind: "possible_postponement",
    confidence: "probable_not_proven",
  },
  {
    productKey: "ref:MAT-1",
    fromRemessa: "2026-11-20",
    toRemessa: "2026-11-15",
    quantityUn: "1",
    kind: "possible_advancement",
    confidence: "probable_not_proven",
  },
];

describe("mywegProbableDateShifts", () => {
  it("calculates calendar day delta without timezone drift", () => {
    expect(calendarDaysBetween("2026-11-12", "2026-11-10")).toBe(-2);
    expect(calendarDaysBetween("2026-11-08", "2026-11-13")).toBe(5);
    expect(calendarDaysBetween("2026-11-08", "2026-11-08")).toBe(0);
  });

  it("formats product keys without claiming unverified identity", () => {
    expect(formatProductKeyForDisplay("code:80016354")).toEqual({
      label: "80016354",
      identityKind: "verified_code",
      confirmed: true,
    });
    expect(formatProductKeyForDisplay("ref:MAT-1").confirmed).toBe(false);
    expect(formatProductKeyForDisplay("informed:XYZ").confirmed).toBe(false);
    expect(formatProductKeyForDisplay("unresolved:empty").label).toContain("não confirmada");
  });

  it("counts kinds without inventing shifts", () => {
    expect(countProbableShiftKinds(sample)).toEqual({
      advancements: 2,
      postponements: 1,
      sameDate: 0,
      total: 3,
    });
    expect(countProbableShiftKinds([])).toEqual({
      advancements: 0,
      postponements: 0,
      sameDate: 0,
      total: 0,
    });
  });

  it("filters locally over the full shift set", () => {
    expect(filterProbableDateShifts(sample, "advancement")).toHaveLength(2);
    expect(filterProbableDateShifts(sample, "postponement")).toHaveLength(1);
    expect(filterProbableDateShifts(sample, "all")).toHaveLength(3);
  });

  it("sorts by nearest remessa date", () => {
    const sorted = sortProbableDateShiftsByNearestRemessa(sample);
    expect(sorted[0]?.productKey).toBe("code:80016355");
    expect(sorted[1]?.productKey).toBe("code:80016354");
  });

  it("tolerates missing probableDateShifts payload", () => {
    expect(normalizeProbableDateShifts(undefined)).toEqual([]);
    expect(normalizeProbableDateShifts(null)).toEqual([]);
    expect(normalizeProbableDateShifts([{ productKey: "code:1" }])).toEqual([]);
    expect(normalizeProbableDateShifts(sample)).toHaveLength(3);
  });
});
