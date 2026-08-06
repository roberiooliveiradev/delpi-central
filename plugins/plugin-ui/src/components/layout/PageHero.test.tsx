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
});
