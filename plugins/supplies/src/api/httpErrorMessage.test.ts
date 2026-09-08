import { describe, expect, it } from "vitest";

import { formatApiErrorBody, resolveHttpErrorMessage } from "./httpErrorMessage";

describe("httpErrorMessage", () => {
  it("keeps supplies-api detail+code", () => {
    expect(formatApiErrorBody({ detail: "Not Found", code: "not_found" }, "x")).toBe(
      "[not_found] Not Found",
    );
  });

  it("does not leak gateway HTML", () => {
    expect(resolveHttpErrorMessage(502, "<!doctype html><html>bad gateway</html>")).toMatch(
      /indisponível/i,
    );
  });
});
