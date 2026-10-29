import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { CreateItemsSection } from "./HelpdeskPage";

const baseProps = {
  sessionCtx: null,
  disabled: false,
  open: true,
  onToggle: () => undefined,
  scope: "mine" as const,
  onScopeChange: () => undefined,
  typeFilter: "",
  onTypeFilterChange: () => undefined,
  query: "",
  onQueryChange: () => undefined,
  results: [],
  searching: false,
  searched: false,
  searchError: null,
  selections: [],
  related: [],
  relatedInput: "",
  onRelatedInputChange: () => undefined,
  onSearchItems: () => undefined,
  onAddItem: () => undefined,
  onRemoveItem: () => undefined,
  onAddRelated: () => undefined,
  onRemoveRelated: () => undefined,
};

describe("HELPDESK-P0 CreateItemsSection render", () => {
  it("expanded section renders without ReferenceError (relatedSearching declared)", () => {
    // Reproduces the black-screen regression: the expanded related-ticket
    // block reads the relatedSearching flag; before the fix the identifier
    // was undeclared and React render threw.
    const html = renderToString(createElement(CreateItemsSection, baseProps));
    expect(html).toContain("Buscar chamado");
    expect(html).toContain("Itens e chamados relacionados");
  });

  it("collapsed section with selections still renders the count badge", () => {
    const html = renderToString(
      createElement(CreateItemsSection, {
        ...baseProps,
        open: false,
        related: [{ id: 7, title: "Chamado A" }],
      }),
    );
    expect(html).toContain("helpdesk-create-items__count");
  });
});
