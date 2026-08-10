import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { MouseEvent } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PagePath,
  isSafeNavigationHref,
  pagePathBemClasses,
} from "./PagePath";

afterEach(cleanup);

const classNames = pagePathBemClasses("cm");

describe("PagePath", () => {
  it("renderiza nav + ol, anchors reais e atual sem repetir limites", () => {
    render(
      <PagePath
        classNames={classNames}
        back={{ label: "Pedidos", href: "/pedidos" }}
        items={[
          { id: "duplicate-back", label: "Pedidos", href: "/pedidos" },
          { id: "customer", label: "Cliente", href: "/clientes/42" },
          { id: "duplicate-current", label: "Pedido 123", href: "/pedidos/123" },
        ]}
        current="Pedido 123"
      />,
    );

    expect(screen.getByRole("navigation", { name: "Caminho da página" })).toBeTruthy();
    expect(document.querySelector("ol")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Pedidos" }).getAttribute("href")).toBe(
      "/pedidos",
    );
    expect(screen.getByRole("link", { name: "Cliente" }).getAttribute("href")).toBe(
      "/clientes/42",
    );
    expect(screen.getAllByText("Pedidos")).toHaveLength(1);
    expect(screen.getAllByText("Pedido 123")).toHaveLength(1);
    expect(screen.getByText("Pedido 123").getAttribute("aria-current")).toBe("page");
    expect(document.querySelector(".cm-page-path")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-page-path")).toBeTruthy();
  });

  it("move ancestrais excedentes para painel com dismiss por Escape", () => {
    const onNavigate = vi.fn((event: MouseEvent<HTMLAnchorElement>) =>
      event.preventDefault(),
    );
    render(
      <PagePath
        classNames={classNames}
        back={{ label: "Início", href: "/" }}
        items={[
          { id: "a", label: "Área", href: "/area", onNavigate },
          { id: "b", label: "Fila", href: "/area/fila" },
        ]}
        current="Registro"
        maxVisibleItems={2}
      />,
    );

    const trigger = screen.getByRole("button", { name: "Mostrar páginas anteriores" });
    fireEvent.click(trigger);
    expect(screen.getByRole("menu", { name: "Páginas anteriores" })).toBeTruthy();
    expect(screen.getByRole("menuitem", { name: "Área" }).getAttribute("href")).toBe(
      "/area",
    );

    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("menu", { name: "Páginas anteriores" })).toBeNull();
  });

  it("aceita somente paths internos ao host", () => {
    expect(isSafeNavigationHref("/apps/commercial/pedidos/123")).toBe(true);
    expect(isSafeNavigationHref("pedidos/123")).toBe(false);
    expect(isSafeNavigationHref("https://intranet.delpi.local/pedidos")).toBe(false);
    expect(isSafeNavigationHref("//outro-host/pedidos")).toBe(false);
    expect(isSafeNavigationHref("data:text/html,alert(1)")).toBe(false);
    expect(() =>
      render(
        <PagePath
          classNames={classNames}
          back={{ label: "Voltar", href: "javascript:alert(1)" }}
          current="Atual"
        />,
      ),
    ).toThrow(/não é interno/);
  });
});
