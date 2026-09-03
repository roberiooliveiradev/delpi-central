import { describe, expect, it } from "vitest";

import { DELPI_CALLER_APP } from "./httpClient";

describe("httpClient", () => {
  it("usa caller-app my-requests (não api-delpi)", () => {
    expect(DELPI_CALLER_APP).toBe("my-requests");
  });
});
