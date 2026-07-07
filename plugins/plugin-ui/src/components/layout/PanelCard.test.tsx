import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { createInfoGrid } from "./DetailFieldGrid";
import { PanelCard, panelCardBemClasses } from "./PanelCard";

describe("PanelCard", () => {
  it("aplica modificador highlight", () => {
    render(
      <PanelCard title="Cabeçalho" highlight classNames={panelCardBemClasses("pc")}>
        <p>Conteúdo</p>
      </PanelCard>,
    );

    expect(document.querySelector(".pc-card--highlight")).toBeTruthy();
    expect(screen.getByText("Cabeçalho")).toBeTruthy();
  });
});

describe("createInfoGrid", () => {
  it("renderiza dl com itens wide", () => {
    const InfoGrid = createInfoGrid("pc");

    render(
      <InfoGrid
        items={[
          { label: "Cliente", value: "ACME" },
          { label: "Observação", value: "Texto longo", wide: true },
        ]}
      />,
    );

    expect(document.querySelector(".pc-info-grid__item--wide")).toBeTruthy();
    expect(screen.getByText("ACME")).toBeTruthy();
  });
});
