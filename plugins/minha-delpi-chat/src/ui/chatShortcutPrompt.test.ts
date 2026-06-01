import { describe, expect, it } from "vitest";

import {
  fillShortcutTemplate,
  formatShortcutTemplateForDisplay,
  hasShortcutPlaceholders,
  hasUnresolvedShortcutPlaceholders,
  listShortcutFieldIds,
  normalizeShortcutTemplate,
  resolveShortcutFields,
  resolveStarterPromptOptions,
  resolveStarterQueryForFeature,
  starterRequiresShortcutModal,
  validateShortcutValues,
  SEARCH_QUERY_PLACEHOLDER,
  WEB_SEARCH_STARTER_QUERY,
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

  it("resolve novidade de pesquisa web para template com placeholder", () => {
    expect(
      resolveStarterQueryForFeature("Pesquise na web sobre manual WEG", {
        featureId: "web_search",
      }),
    ).toBe(WEB_SEARCH_STARTER_QUERY);
    expect(
      resolveStarterQueryForFeature("consultar produto", { starterId: "product" }),
    ).toBe("consultar produto");
  });

  it("detecta quando o atalho da home exige modal", () => {
    expect(
      starterRequiresShortcutModal("qual o estoque do produto {{productCode}}?", {
        starterId: "stock",
      }),
    ).toBe(true);
    expect(
      starterRequiresShortcutModal("mostre KPIs comerciais do mês passado", {
        starterId: "kpi",
      }),
    ).toBe(false);
    expect(starterRequiresShortcutModal("estoque do {product_code}", { starterId: "stock" })).toBe(
      true,
    );
  });

  it("escolhe diálogo por tipo de atalho", () => {
    expect(
      resolveStarterPromptOptions("pesquise na web sobre {{searchQuery}}", {
        featureId: "web_search",
      }).title,
    ).toBe("Pesquisa na web");
    expect(
      resolveStarterPromptOptions(
        "escreva um e-mail formal para {{emailRecipient}} sobre {{emailSubject}}",
        { starterId: "email" },
      ).title,
    ).toBe("E-mail formal");
    expect(
      resolveStarterPromptOptions("me fale do produto {{productCode}}", {
        starterId: "product",
      }).title,
    ).toBe("Consulta operacional");
  });

  it("usa Ex.: DELPI Conexões Elétricas no placeholder de pesquisa web", () => {
    const fields = resolveShortcutFields("pesquise na web sobre {{searchQuery}}");
    const searchField = fields.find((field) => field.id === "searchQuery");

    expect(searchField?.placeholder).toBe(SEARCH_QUERY_PLACEHOLDER);
    expect(SEARCH_QUERY_PLACEHOLDER).toBe("Ex.: DELPI Conexões Elétricas");
  });

  it("substitui {{campo}} por dica legível na exibição", () => {
    expect(formatShortcutTemplateForDisplay("me fale do produto {{productCode}}")).toBe(
      "me fale do produto Ex.: 10080001",
    );
    expect(formatShortcutTemplateForDisplay("pesquise na web sobre {{searchQuery}}")).toBe(
      `pesquise na web sobre ${SEARCH_QUERY_PLACEHOLDER}`,
    );
    expect(formatShortcutTemplateForDisplay("o que você pode fazer?")).toBe(
      "o que você pode fazer?",
    );
  });
});
