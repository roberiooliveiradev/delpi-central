import { describe, expect, it } from "vitest";

import {
  PROCESS_ISSUE_CREATE_PERMISSION,
  canCreateProcessIssue,
} from "./processIssue";

describe("canCreateProcessIssue", () => {
  it("libera para superadmin mesmo sem o código", () => {
    expect(canCreateProcessIssue([], true)).toBe(true);
  });

  it("libera quando o código efetivo está presente", () => {
    expect(
      canCreateProcessIssue(
        ["production-control.access", PROCESS_ISSUE_CREATE_PERMISSION],
        false,
      ),
    ).toBe(true);
  });

  it("nega sem o código e sem superadmin (sibling general-request não basta)", () => {
    expect(
      canCreateProcessIssue(
        [
          "production-control.access",
          "my-requests.general-request.create",
          "my-requests.process-issue.process",
        ],
        false,
      ),
    ).toBe(false);
  });
});
