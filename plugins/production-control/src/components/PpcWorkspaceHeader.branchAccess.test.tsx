// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PpcAllowedBranchesProvider } from "../branchAccessContext";
import { PpcWorkspaceHeader } from "./PpcWorkspaceHeader";

vi.mock("./LineFeederUrgentBell", () => ({
  LineFeederUrgentBell: ({ branch }: { branch: string }) => (
    <span data-testid="ppc-global-operational-bell">{branch}</span>
  ),
}));

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
  it("renderiza o sino global em qualquer workspace autorizado e sem duplicidade", () => {
    const { rerender } = render(
      <PpcAllowedBranchesProvider
        allowedBranches={["02"]}
        featureAccess={{ canViewLineFeeder: true, canViewMyWeg: true }}
      >
        <PpcWorkspaceHeader title="Demanda" branch="02" subpluginId="demand" />
      </PpcAllowedBranchesProvider>,
    );
    expect(screen.getAllByTestId("ppc-global-operational-bell")).toHaveLength(1);

    rerender(
      <PpcAllowedBranchesProvider
        allowedBranches={["02"]}
        featureAccess={{ canViewLineFeeder: true, canViewMyWeg: true }}
      >
        <PpcWorkspaceHeader title="Materiais" branch="02" subpluginId="materials" />
      </PpcAllowedBranchesProvider>,
    );
    expect(screen.getAllByTestId("ppc-global-operational-bell")).toHaveLength(1);
  });

  it("filial 01 não recebe alerta MyWEG e não expõe sino sem autorização", () => {
    const { rerender } = render(
      <PpcAllowedBranchesProvider
        allowedBranches={["01"]}
        featureAccess={{ canViewLineFeeder: false, canViewMyWeg: true }}
      >
        <PpcWorkspaceHeader title="Demanda" branch="01" subpluginId="demand" />
      </PpcAllowedBranchesProvider>,
    );
    expect(screen.queryByTestId("ppc-global-operational-bell")).toBeNull();

    rerender(
      <PpcAllowedBranchesProvider
        allowedBranches={["02"]}
        featureAccess={{ canViewLineFeeder: false, canViewMyWeg: true }}
      >
        <PpcWorkspaceHeader title="Demanda" branch="02" subpluginId="demand" />
      </PpcAllowedBranchesProvider>,
    );
    expect(screen.getAllByTestId("ppc-global-operational-bell")).toHaveLength(1);
  });
});
