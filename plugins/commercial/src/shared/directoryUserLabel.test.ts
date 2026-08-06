import { describe, expect, it } from "vitest";

import {
  directoryUserLabelOrFallback,
  formatDirectoryUserLabel,
  looksLikeUserId,
} from "./directoryUserLabel";

describe("directoryUserLabel", () => {
  it("detects UUID-like ids", () => {
    expect(looksLikeUserId("bb488bd8-3b17-4fd1-8f8e-0510de102f25")).toBe(true);
    expect(looksLikeUserId("João Silva")).toBe(false);
  });

  it("never formats UUID as name or email", () => {
    expect(
      formatDirectoryUserLabel({
        name: "bb488bd8-3b17-4fd1-8f8e-0510de102f25",
        email: "user@delpi.com",
      }),
    ).toBe("user@delpi.com");
  });

  it("falls back without exposing id", () => {
    expect(
      directoryUserLabelOrFallback(
        {},
        "bb488bd8-3b17-4fd1-8f8e-0510de102f25",
      ),
    ).toBe("Usuário");
    expect(directoryUserLabelOrFallback({}, "Usuário Comum")).toBe("Usuário Comum");
  });
});
