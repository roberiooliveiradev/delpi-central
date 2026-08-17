import { describe, expect, it } from "vitest";

import {
  layoutOrgMembershipForest,
  ORG_MEMBERSHIP_NODE_HEIGHT,
  ORG_MEMBERSHIP_V_GAP,
} from "./layoutOrgMembershipForest";

describe("layoutOrgMembershipForest", () => {
  it("places roots at depth 0 and children below", () => {
    const positions = layoutOrgMembershipForest(
      [{ id: "p1" }, { id: "u1" }, { id: "u2" }],
      [
        { source: "p1", target: "u1" },
        { source: "p1", target: "u2" },
      ],
    );
    expect(positions.get("p1")?.y).toBe(0);
    expect(positions.get("u1")?.y).toBe(ORG_MEMBERSHIP_NODE_HEIGHT + ORG_MEMBERSHIP_V_GAP);
    expect(positions.get("u2")?.y).toBe(ORG_MEMBERSHIP_NODE_HEIGHT + ORG_MEMBERSHIP_V_GAP);
    expect(positions.get("u1")?.x).not.toEqual(positions.get("u2")?.x);
  });

  it("layouts a forest of independent roots side by side", () => {
    const positions = layoutOrgMembershipForest(
      [{ id: "a" }, { id: "b" }, { id: "c" }],
      [{ source: "a", target: "c" }],
    );
    expect(positions.get("a")?.y).toBe(0);
    expect(positions.get("b")?.y).toBe(0);
    expect((positions.get("b")?.x ?? 0) > (positions.get("a")?.x ?? 0)).toBe(true);
    expect(positions.get("c")?.y).toBe(ORG_MEMBERSHIP_NODE_HEIGHT + ORG_MEMBERSHIP_V_GAP);
  });

  it("places orphan nodes without edges", () => {
    const positions = layoutOrgMembershipForest([{ id: "solo" }], []);
    expect(positions.get("solo")).toEqual({ x: 0, y: 0 });
  });
});
