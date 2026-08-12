import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CatalogSearchBar, catalogSearchBarBemClasses } from "./CatalogSearchBar";

afterEach(() => {
  cleanup();
});

describe("CatalogSearchBar", () => {
  it("chama onChange ao digitar", () => {
    const onChange = vi.fn();
    render(
      <CatalogSearchBar
        classNames={catalogSearchBarBemClasses("cm")}
        value=""
        onChange={onChange}
        placeholder="Buscar"
        aria-label="Buscar caminhos"
      />,
    );
    fireEvent.change(screen.getByRole("combobox", { name: "Buscar caminhos" }), {
      target: { value: "prop" },
    });
    expect(onChange).toHaveBeenCalledWith("prop");
  });

  it("seleciona hit e limpa com Esc via clear implícito no Escape com valor", () => {
    const onChange = vi.fn();
    const onSelectHit = vi.fn();
    const { rerender } = render(
      <CatalogSearchBar
        classNames={catalogSearchBarBemClasses("cm")}
        value="pro"
        onChange={onChange}
        onSelectHit={onSelectHit}
        hits={[{ id: "proposals", label: "Propostas", groupLabel: "Documentos" }]}
        aria-label="Buscar"
      />,
    );
    fireEvent.focus(screen.getByRole("combobox"));
    fireEvent.click(screen.getByRole("option", { name: /Propostas/ }));
    expect(onSelectHit).toHaveBeenCalledWith("proposals");

    rerender(
      <CatalogSearchBar
        classNames={catalogSearchBarBemClasses("cm")}
        value="pro"
        onChange={onChange}
        aria-label="Buscar"
      />,
    );
    fireEvent.keyDown(screen.getByRole("combobox"), { key: "Escape" });
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("expõe field dual-class para foco no container", () => {
    const { container } = render(
      <CatalogSearchBar
        classNames={catalogSearchBarBemClasses("cm")}
        value=""
        onChange={() => undefined}
        aria-label="Buscar"
      />,
    );
    expect(container.querySelector(".delpi-ui-catalog-search-bar__field")).toBeTruthy();
    expect(container.querySelector(".cm-catalog-search__field")).toBeTruthy();
  });
});
