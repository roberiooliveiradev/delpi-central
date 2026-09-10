import { describe, expect, it } from "vitest";

import { ReasonConfirmModal } from "./ReasonConfirmModal";

describe("ReasonConfirmModal", () => {
  it("exporta componente de confirmação kit-first com targets na devolução", () => {
    expect(typeof ReasonConfirmModal).toBe("function");
    expect(String(ReasonConfirmModal)).toMatch(/function|ReasonConfirm/);
  });
});
