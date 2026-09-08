import { describe, expect, it } from "vitest";

import {
  branchCodeForCreate,
  normalizeBranchScope,
  requiresBranchField,
  showsBranchField,
} from "./branchScope";

describe("branchScope", () => {
  it("normaliza e classifica escopos", () => {
    expect(normalizeBranchScope("required")).toBe("required");
    expect(normalizeBranchScope("NONE")).toBe("none");
    expect(normalizeBranchScope(undefined)).toBe("optional");
    expect(showsBranchField("none")).toBe(false);
    expect(showsBranchField("optional")).toBe(true);
    expect(requiresBranchField("required")).toBe(true);
    expect(requiresBranchField("optional")).toBe(false);
  });

  it("omite branch no create quando none", () => {
    expect(branchCodeForCreate("none", "01")).toBeUndefined();
    expect(branchCodeForCreate("required", "01")).toBe("01");
    expect(branchCodeForCreate("required", "")).toBeUndefined();
  });
});
