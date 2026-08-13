import { describe, expect, it } from "vitest";

import { orgMembershipFlowBemClasses } from "./orgMembershipFlowTypes";

describe("orgMembershipFlowBemClasses", () => {
  it("inclui dual-class para nó group", () => {
    const classes = orgMembershipFlowBemClasses("cm");
    expect(classes.nodeGroup).toBe(
      "cm-org-flow__node--group delpi-ui-org-flow__node--group",
    );
  });
});
