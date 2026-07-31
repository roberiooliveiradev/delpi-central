import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TvLibraryPageLayout } from "./TvLibraryPageLayout";

describe("TvLibraryPageLayout", () => {
  afterEach(() => {
    cleanup();
  });

  it("renderiza slots header, actions, toolbar e children", () => {
    const { container } = render(
      <TvLibraryPageLayout
        header={<h1>Cabeçalho</h1>}
        actions={<button type="button">Ação</button>}
        toolbar={<div>Filtros</div>}
      >
        <p>Conteúdo</p>
      </TvLibraryPageLayout>,
    );

    expect(container.querySelector(".td-page-stack")).toBeTruthy();
    expect(container.querySelector(".td-action-grid")).toBeTruthy();
    expect(container.querySelector(".td-library-toolbar")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Cabeçalho" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Ação" })).toBeTruthy();
    expect(screen.getByText("Filtros")).toBeTruthy();
    expect(screen.getByText("Conteúdo")).toBeTruthy();
  });

  it("omite action/toolbar quando ausentes", () => {
    const { container } = render(
      <TvLibraryPageLayout header={<h1>Só header</h1>}>
        <p>Body</p>
      </TvLibraryPageLayout>,
    );

    expect(container.querySelector(".td-action-grid")).toBeNull();
    expect(container.querySelector(".td-library-toolbar")).toBeNull();
  });
});
