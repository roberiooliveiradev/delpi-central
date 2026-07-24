import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import {
  PageHeader,
  pageHeaderBrandBemClasses,
  pageHeaderTitleRowBemClasses,
} from "./PageHeader";

afterEach(() => {
  cleanup();
});

describe("PageHeader", () => {
  it("emite dual-class e slot nav no layout titleRow", () => {
    const { container } = render(
      <PageHeader
        layout="titleRow"
        classNames={pageHeaderTitleRowBemClasses("cipa")}
        labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
        nav={<button type="button">Unidades</button>}
        title="CIPA — Santa Catarina"
        subtitle="Atas de reunião da unidade"
        actions={<button type="button">Nova ata</button>}
      />,
    );

    expect(container.querySelector(".delpi-ui-page-header")).toBeTruthy();
    expect(container.querySelector(".cipa-page-header")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "CIPA — Santa Catarina" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Unidades" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova ata" })).toBeTruthy();
  });

  it("hideHeading omite h1 e subtítulo no layout brand", () => {
    render(
      <PageHeader
        layout="brand"
        classNames={pageHeaderBrandBemClasses("ds")}
        labels={{ refresh: "Atualizar", refreshing: "Atualizando…" }}
        eyebrow="DELPI • Transformômetro"
        title="Dashboard Transformômetro"
        subtitle="Economia bruta e líquida"
        hideHeading
        nav={<button type="button">Dashboard</button>}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Dashboard Transformômetro" })).toBeNull();
    expect(screen.queryByText("Economia bruta e líquida")).toBeNull();
    expect(screen.getByRole("banner", { name: "Dashboard Transformômetro" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Dashboard" })).toBeTruthy();
    expect(screen.getByText("DELPI • Transformômetro")).toBeTruthy();
  });
});
