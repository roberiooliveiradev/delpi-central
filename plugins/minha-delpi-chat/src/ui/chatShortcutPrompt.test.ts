import { describe, expect, it } from "vitest";

import {
  fillShortcutTemplate,
  formatShortcutTemplateForDisplay,
  hasShortcutPlaceholders,
  hasUnresolvedShortcutPlaceholders,
  listShortcutFieldIds,
  normalizeShortcutTemplate,
  resolveShortcutFields,
  validateShortcutValues,
} from "./chatShortcutPrompt";

describe("chatShortcutPrompt", () => {
  it("detecta placeholders no template", () => {
    expect(hasShortcutPlaceholders("estoque do produto {{productCode}}")).toBe(true);
    expect(hasShortcutPlaceholders("o que você pode fazer?")).toBe(false);
    expect(hasUnresolvedShortcutPlaceholders("produto {{productCode}}")).toBe(true);
    expect(hasUnresolvedShortcutPlaceholders("produto 10080001")).toBe(false);
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

  it("lista campos após hasShortcutPlaceholders sem corromper regex global", () => {
    const query = "me fale do produto {{productCode}}";

    expect(hasShortcutPlaceholders(query)).toBe(true);
    expect(listShortcutFieldIds(query)).toEqual(["productCode"]);
    expect(resolveShortcutFields(query)).toHaveLength(1);
  });

  it("substitui {{campo}} por dica legível na exibição", () => {
    expect(formatShortcutTemplateForDisplay("me fale do produto {{productCode}}")).toBe(
      "me fale do produto Ex.: 10080001",
    );
    expect(formatShortcutTemplateForDisplay("pesquise na web sobre {{searchQuery}}")).toBe(
      "pesquise na web sobre Ex.: manual WEG CFW500",
    );
    expect(formatShortcutTemplateForDisplay("o que você pode fazer?")).toBe(
      "o que você pode fazer?",
    );
  });
});
