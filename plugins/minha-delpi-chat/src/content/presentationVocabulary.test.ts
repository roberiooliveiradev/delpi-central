import { describe, expect, it } from "vitest";

import {
  formatRichToolbarTemplate,
  richPresentationToolbar,
} from "./presentationVocabulary";

describe("presentationVocabulary richPresentationToolbar", () => {
  it("expõe chaves de busca/filtro/footer", () => {
    const toolbar = richPresentationToolbar();

    expect(toolbar.searchPlaceholderTable.length).toBeGreaterThan(0);
    expect(toolbar.searchPlaceholderTree.length).toBeGreaterThan(0);
    expect(toolbar.filterContainsLabel).toBe("Contém");
    expect(toolbar.exportReflectsFiltersHint.length).toBeGreaterThan(0);
  });

  it("formata templates de footer", () => {
    expect(
      formatRichToolbarTemplate(richPresentationToolbar().footerTableFiltered, {
        visible: 3,
        total: 46,
      }),
    ).toBe("3 de 46 registro(s)");
  });
});
