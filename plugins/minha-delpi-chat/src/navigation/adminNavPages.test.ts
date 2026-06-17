import { describe, expect, it } from "vitest";

import { defaultPageForSubTab, nestedPageFromSlug, nestedPageSlug } from "./adminNavPages";

describe("adminNavPages", () => {
  it("resolve slug e chave de páginas de aprendizagem", () => {
    expect(nestedPageSlug("learning", "finetuning")).toBe("ajuste-fino");
    expect(nestedPageFromSlug("learning", "ajuste-fino")).toBe("finetuning");
    expect(defaultPageForSubTab("learning")).toBe("pipeline");
  });
});
