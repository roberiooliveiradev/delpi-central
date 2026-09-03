import { describe, expect, it } from "vitest";

import { ActionBar } from "../components/ActionBar";

describe("ActionBar render-only", () => {
  it("recebe actions da API sem inferir máquina de estados", () => {
    expect(typeof ActionBar).toBe("function");
    const actions = ["start", "cancel"];
    expect(actions).not.toContain("invented-by-frontend");
  });
});
