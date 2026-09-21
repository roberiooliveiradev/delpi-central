import { describe, expect, it } from "vitest";

import {
  formatEntityCodeStoreCenter,
  formatEntityTypeWithCodeStoreCenter,
} from "./entityCodeStore";

describe("entityCodeStore center identity", () => {
  it("junta código-loja e centro na identidade do cliente", () => {
    expect(formatEntityCodeStoreCenter("000001", "09", "1106")).toBe(
      "000001-09 · 1106",
    );
    expect(formatEntityCodeStoreCenter("000001", "09", null)).toBe("000001-09");
    expect(
      formatEntityTypeWithCodeStoreCenter("CLIENTE", "000001", "09", "1106"),
    ).toBe("CLIENTE 000001-09 · 1106");
  });
});
