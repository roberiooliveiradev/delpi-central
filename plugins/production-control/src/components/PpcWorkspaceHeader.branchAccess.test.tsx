// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PpcAllowedBranchesProvider } from "../branchAccessContext";
import { PpcWorkspaceHeader } from "./PpcWorkspaceHeader";

vi.mock("@delpi/plugin-ui/index", () => ({
  HelpTooltip: () => null,
  DelpiLogoMark: () => null,
}));

afterEach(() => {
  cleanup();
});

describe("PpcWorkspaceHeader — branch access", () => {
  it("P0: com uma filial só mostra o rótulo, sem botão da outra", () => {
    render(
      <PpcAllowedBranchesProvider allowedBranches={["02"]}>
        <PpcWorkspaceHeader title="Gestão à vista" branch="02" subpluginId="home" />
      </PpcAllowedBranchesProvider>,
    );

    expect(screen.getByText("ES · 02")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "SC · 01" })).toBeNull();
    expect(screen.queryByRole("button", { name: "ES · 02" })).toBeNull();
  });

  it("irmão: só filial 01", () => {
    render(
      <PpcAllowedBranchesProvider allowedBranches={["01"]}>
        <PpcWorkspaceHeader title="Gestão à vista" branch="01" subpluginId="home" />
      </PpcAllowedBranchesProvider>,
    );

    expect(screen.getByText("SC · 01")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "ES · 02" })).toBeNull();
  });

  it("negativo: com ambas as filiais o seletor continua clicável", () => {
    render(
      <PpcAllowedBranchesProvider allowedBranches={["01", "02"]}>
        <PpcWorkspaceHeader title="Gestão à vista" branch="01" subpluginId="home" />
      </PpcAllowedBranchesProvider>,
    );

    expect(screen.getByRole("button", { name: "SC · 01" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "ES · 02" })).toBeTruthy();
  });

  it("appearance myweg aplica a classe do banner só nesse menu", () => {
    const { container, rerender } = render(
      <PpcAllowedBranchesProvider allowedBranches={["02"]}>
        <PpcWorkspaceHeader
          title="Necessidades WEG"
          branch="02"
          subpluginId="myweg-needs"
          appearance="myweg"
        />
      </PpcAllowedBranchesProvider>,
    );

    expect(container.querySelector("header.ppc-header--myweg")).toBeTruthy();

    rerender(
      <PpcAllowedBranchesProvider allowedBranches={["02"]}>
        <PpcWorkspaceHeader title="Gestão à vista" branch="02" subpluginId="home" />
      </PpcAllowedBranchesProvider>,
    );
    expect(container.querySelector("header.ppc-header--myweg")).toBeNull();
  });
});
