import { describe, expect, it } from "vitest";

import {
  fillShortcutTemplate,
  hasShortcutPlaceholders,
  listShortcutFieldIds,
  normalizeShortcutTemplate,
  resolveShortcutFields,
  validateShortcutValues,
} from "./chatShortcutPrompt";

describe("chatShortcutPrompt", () => {
  it("detecta placeholders no template", () => {
    expect(hasShortcutPlaceholders("estoque do produto {{productCode}}")).toBe(true);
    expect(hasShortcutPlaceholders("o que você pode fazer?")).toBe(false);
  });

  it("normaliza legado do playbook", () => {
    expect(normalizeShortcutTemplate("estoque do {product_code}")).toBe(
      "estoque do {{productCode}}",
    );
  });

  it("preenche template com valores informados", () => {
    const filled = fillShortcutTemplate("estoque do produto {{productCode}}", {
      productCode: "10080099",
    });

    expect(filled).toBe("estoque do produto 10080099");
  });

  it("valida código de produto", () => {
    const fields = resolveShortcutFields("produto {{productCode}}");
    const errors = validateShortcutValues(fields, { productCode: "abc" });

    expect(errors?.productCode).toBeTruthy();
  });

  it("lista campos únicos na ordem do template", () => {
    expect(
      listShortcutFieldIds("{{searchQuery}} e {{productCode}}"),
    ).toEqual(["searchQuery", "productCode"]);
  });
});
