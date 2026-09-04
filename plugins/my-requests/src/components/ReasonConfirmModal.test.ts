import { describe, expect, it } from "vitest";

import { ReasonConfirmModal } from "./ReasonConfirmModal";

describe("ReasonConfirmModal", () => {
  it("exporta componente de confirmação kit-first", () => {
    expect(typeof ReasonConfirmModal).toBe("function");
  });
});
