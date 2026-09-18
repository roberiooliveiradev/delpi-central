import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  TopBarFavoritesStrip,
  createDashboardTopBarFavoritesStrip,
  topBarFavoritesStripBemClasses,
} from "./TopBarFavoritesStrip";
import { TopBarUtilityCluster, topBarUtilityClusterBemClasses } from "./TopBarUtilityCluster";

afterEach(() => {
  cleanup();
});

describe("TopBarFavoritesStrip", () => {
  it("mostra vazio, abre painel e seleciona item", () => {
    const onSelect = vi.fn();
    const onRemove = vi.fn();
    const { rerender } = render(
      <TopBarFavoritesStrip
        classNames={topBarFavoritesStripBemClasses("cm")}
        items={[]}
        onSelect={onSelect}
        onRemove={onRemove}
        title="Favoritos"
        emptyLabel="Nenhum favorito."
        openAriaLabel="Abrir favoritos"
        closeAriaLabel="Fechar favoritos"
        removeLabel={(label) => `Remover ${label}`}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Abrir favoritos" }));
    expect(screen.getByText("Nenhum favorito.")).toBeTruthy();

    rerender(
      <TopBarFavoritesStrip
        classNames={topBarFavoritesStripBemClasses("cm")}
        items={[{ id: "/home", label: "Início" }]}
        onSelect={onSelect}
        onRemove={onRemove}
        title="Favoritos"
        emptyLabel="Nenhum favorito."
        openAriaLabel="Abrir favoritos"
        closeAriaLabel="Fechar favoritos"
        removeLabel={(label) => `Remover ${label}`}
      />,
    );
    fireEvent.click(screen.getByRole("menuitem", { name: "Início" }));
    expect(onSelect).toHaveBeenCalledWith("/home");
  });

  it("emite dual-class e remove item sem persistir regra", () => {
    const onRemove = vi.fn();
    const { container } = render(
      <TopBarUtilityCluster classNames={topBarUtilityClusterBemClasses("cm")}>
        <TopBarFavoritesStrip
          classNames={topBarFavoritesStripBemClasses("cm")}
          items={[{ id: "tasks", label: "Minhas tarefas" }]}
          onSelect={() => undefined}
          onRemove={onRemove}
          title="Favoritos"
          emptyLabel="Nenhum favorito."
          openAriaLabel="Abrir favoritos"
          closeAriaLabel="Fechar favoritos"
          removeLabel={(label) => `Remover ${label}`}
        />
      </TopBarUtilityCluster>,
    );
    expect(container.querySelector(".delpi-ui-topbar-utility")).toBeTruthy();
    expect(container.querySelector(".cm-topbar-favorites")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-topbar-favorites__trigger")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir favoritos" }));
    fireEvent.click(screen.getByRole("button", { name: "Remover Minhas tarefas" }));
    expect(onRemove).toHaveBeenCalledWith("tasks");
  });

  it("factory injeta classNames", () => {
    const Strip = createDashboardTopBarFavoritesStrip({ prefix: "sp" });
    const { container } = render(
      <Strip
        items={[]}
        onSelect={() => undefined}
        onRemove={() => undefined}
        title="Favoritos"
        emptyLabel="Vazio"
        openAriaLabel="Abrir favoritos"
        closeAriaLabel="Fechar favoritos"
        removeLabel={(label) => label}
      />,
    );
    expect(container.querySelector(".sp-topbar-favorites")).toBeTruthy();
  });
});
