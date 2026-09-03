/**
 * Gate local — hierarquia de áreas (folhas vs agregadoras).
 * Uso: node --experimental-strip-types scripts/check-audit-areas-hierarchy.ts
 */
import type { AuditArea } from "../src/api/audit5sApi.ts";
import {
  eligibleSubAreaCandidates,
  leafAreas,
  ungroupedLeafAreas,
} from "../src/utils/auditAreasHierarchy.ts";

const areas: AuditArea[] = [
  {
    id: "p1",
    branch_code: "02",
    name: "Agregadora",
    active: true,
    is_aggregator: true,
    children_count: 1,
  },
  {
    id: "c1",
    branch_code: "02",
    name: "Sub",
    active: true,
    parent_area_id: "p1",
    is_sub_area: true,
    children_count: 0,
  },
  {
    id: "loose",
    branch_code: "02",
    name: "Solta",
    active: true,
    children_count: 0,
  },
];

function assertEqual(actual: unknown, expected: unknown, label: string) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    throw new Error(`${label}: expected ${e}, got ${a}`);
  }
}

assertEqual(
  leafAreas(areas).map((a) => a.id),
  ["c1", "loose"],
  "leafAreas",
);
assertEqual(
  ungroupedLeafAreas(areas).map((a) => a.id),
  ["loose"],
  "ungroupedLeafAreas",
);
assertEqual(
  eligibleSubAreaCandidates(areas, "p1").map((a) => a.id),
  ["c1", "loose"],
  "eligibleSubAreaCandidates",
);

console.log("check-audit-areas-hierarchy: ok");
