import { describe, expect, it } from "vitest";

import { buildQuery } from "./queryParams";

describe("buildQuery", () => {
  it("omits empty values so the BFF does not receive blank filters", () => {
    expect(buildQuery({ branch: "01", search: "", page: 1, refresh: null })).toBe(
      "?branch=01&page=1",
    );
  });

  it("returns an empty string when nothing is set", () => {
    expect(buildQuery({ branch: null, search: undefined })).toBe("");
  });
});
