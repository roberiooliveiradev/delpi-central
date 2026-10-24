import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { PageHero, pageHeroBemClasses } from "./PageHero";

describe("PageHero", () => {
  it("emite dual-class BEM", () => {
    const cn = pageHeroBemClasses("cm");
    expect(cn.root).toContain("cm-page-hero");
    expect(cn.root).toContain("delpi-ui-page-hero");
    expect(cn.title).toContain("delpi-ui-page-hero__title");
  });

  it("renderiza eyebrow, título, descrição e highlights", () => {
    const cn = pageHeroBemClasses("cm");
    render(
      <PageHero
        classNames={cn}
        eyebrow="Portal Comercial"
        title="Boa tarde, Ana"
        description="Bem vindo."
        highlights={[{ id: "a", label: "Pedidos", value: "10" }]}
      />,
    );
    expect(screen.getByText("Portal Comercial")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Boa tarde, Ana" })).toBeTruthy();
    expect(screen.getByText("Bem vindo.")).toBeTruthy();
    expect(screen.getByText("Pedidos")).toBeTruthy();
    expect(screen.getByText("10")).toBeTruthy();
  });

  it("aplica tone warning no highlight", () => {
    const cn = pageHeroBemClasses("cm");
    const { container } = render(
      <PageHero
        classNames={cn}
        title="Início"
        highlights={[{ id: "late", label: "Atrasos", value: "3", tone: "warning" }]}
      />,
    );
    const tile = container.querySelector("[data-tone='warning']");
    expect(tile?.className).toContain("delpi-ui-page-hero__highlight--warning");
    expect(tile?.className).toContain("cm-page-hero__highlight--warning");
  });

  it("renderiza actions e children no body", () => {
    const cn = pageHeroBemClasses("cm");
    render(
      <PageHero
        classNames={cn}
        title="Pedidos"
        actions={<button type="button">Atualizar</button>}
      >
        <p>Filtros aqui</p>
      </PageHero>,
    );
    expect(screen.getByRole("button", { name: "Atualizar" })).toBeTruthy();
    expect(screen.getByText("Filtros aqui")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-page-hero__body")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-page-hero__actions")).toBeTruthy();
  });

  it("renderiza description e loading no highlight", () => {
    const cn = pageHeroBemClasses("cm");
    render(
      <PageHero
        classNames={cn}
        title="Início"
        highlights={[
          {
            id: "economy",
            label: "Economia",
            value: "R$ 10",
            description: "Recorte do mês",
            loading: true,
          },
        ]}
      />,
    );
    expect(screen.getByText("Economia")).toBeTruthy();
    expect(screen.getByText("…")).toBeTruthy();
    expect(screen.getByText("Recorte do mês")).toBeTruthy();
    expect(document.querySelector("[data-loading='true']")).toBeTruthy();
  });

  it("highlight com onSelect vira role=button acionável e pressed", () => {
    const cn = pageHeroBemClasses("cm");
    let selected = 0;
    const { container } = render(
      <PageHero
        classNames={cn}
        title="Início"
        highlights={[
          {
            id: "below",
            label: "Abaixo",
            value: "5",
            onSelect: () => {
              selected += 1;
            },
            active: true,
            ariaLabel: "Filtrar por Abaixo",
          },
          { id: "plain", label: "Neutro", value: "1" },
        ]}
      />,
    );
    const tile = screen.getByRole("button", { name: "Filtrar por Abaixo" });
    expect(tile.getAttribute("aria-pressed")).toBe("true");
    expect(tile.className).toContain("delpi-ui-page-hero__highlight--interactive");
    expect(tile.className).toContain("delpi-ui-page-hero__highlight--pressed");
    expect(tile.className).toContain("cm-page-hero__highlight--interactive");
    tile.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(selected).toBe(1);
    // Tile sem onSelect continua inerte (sem role=button extra).
    expect(container.querySelectorAll("[role='button']").length).toBe(1);
  });

  it("aplica density compact no root", () => {
    const cn = pageHeroBemClasses("cm");
    const { container } = render(
      <PageHero classNames={cn} title="Equipe" density="compact" />,
    );
    const root = container.querySelector("[data-density='compact']");
    expect(root?.className).toContain("delpi-ui-page-hero--compact");
    expect(root?.className).toContain("cm-page-hero--compact");
  });
});
