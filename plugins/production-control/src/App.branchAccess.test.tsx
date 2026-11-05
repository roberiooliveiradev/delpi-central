// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { BRANCH_STORAGE_KEY } from "./constants/routes";

vi.mock("./hooks/useSubplugins", () => ({
  useSubplugins: () => ({ items: [], error: null }),
}));

vi.mock("./components/PpcConfirmDialogProvider", () => ({
  PpcConfirmDialogProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("./components/PpcRail", () => ({
  PpcRail: () => null,
}));

vi.mock("./pages/OverviewPage", () => ({
  OverviewPage: ({ branch }: { branch: string }) => (
    <div data-testid="overview" data-branch={branch}>
      overview-{branch}
    </div>
  ),
}));

vi.mock("./pages/DemandPage", () => ({ DemandPage: () => null }));
vi.mock("./pages/ProblemAnalysisPage", () => ({ ProblemAnalysisPage: () => null }));
vi.mock("./pages/MaterialsPage", () => ({ MaterialsPage: () => null }));
vi.mock("./pages/LineFeederPage", () => ({ LineFeederPage: () => null }));
vi.mock("./pages/MachineLoadPage", () => ({
  MachineLoadPage: ({ branch }: { branch: string }) => (
    <div data-testid="machine-load" data-branch={branch}>
      machine-load-{branch}
    </div>
  ),
}));
vi.mock("./pages/DeliveryMapPage", () => ({ DeliveryMapPage: () => null }));
vi.mock("./pages/ReportsPage", () => ({ ReportsPage: () => null }));
vi.mock("./pages/ProductModelsPage", () => ({ ProductModelsPage: () => null }));
vi.mock("./pages/SequencingProfilesPage", () => ({ SequencingProfilesPage: () => null }));
vi.mock("./pages/MyWegNeedsPage", () => ({ MyWegNeedsPage: () => null }));

function renderApp(pathname: string, permissions: string[], isSuperadmin = false) {
  window.history.pushState({}, "", pathname);
  return render(
    <App permissions={permissions} isSuperadmin={isSuperadmin} getAccessToken={() => "token"} />,
  );
}

describe("App — branch access", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  afterEach(() => {
    cleanup();
    window.sessionStorage.clear();
  });

  it("P0: usuário só com filial 02 não fica preso em 01", async () => {
    renderApp("/apps/production-control", [
      "production-control.access",
      "production-control.view.filial-02",
    ]);

    await waitFor(() => {
      expect(window.location.search).toBe("?branch=02");
    });
    expect(window.sessionStorage.getItem(BRANCH_STORAGE_KEY)).toBe("02");
    expect(screen.getByTestId("overview").getAttribute("data-branch")).toBe("02");
  });

  it("irmão: usuário só com filial 01 permanece em 01", async () => {
    renderApp("/apps/production-control?branch=01", [
      "production-control.access",
      "production-control.view.filial-01",
    ]);

    await waitFor(() => {
      expect(screen.getByTestId("overview").getAttribute("data-branch")).toBe("01");
    });
    expect(window.location.search).toBe("?branch=01");
  });

  it("negativo: deep link em filial sem permissão é canonizado", async () => {
    window.sessionStorage.setItem(BRANCH_STORAGE_KEY, "01");
    renderApp("/apps/production-control/machine-load?branch=01&ct=CT-01", [
      "production-control.access",
      "production-control.view.filial-02",
    ]);

    await waitFor(() => {
      expect(window.location.pathname).toBe("/apps/production-control/machine-load");
      expect(window.location.search).toBe("?branch=02&ct=CT-01");
    });
    expect(screen.getByTestId("machine-load").getAttribute("data-branch")).toBe("02");
  });

  it("ambas as filiais: mantém a preferência da URL", async () => {
    renderApp("/apps/production-control?branch=02", [
      "production-control.access",
      "production-control.view.filial-01",
      "production-control.view.filial-02",
    ]);

    await waitFor(() => {
      expect(screen.getByTestId("overview").getAttribute("data-branch")).toBe("02");
    });
  });

  it("sem filial: mostra bloqueio e não inventa 01", async () => {
    renderApp("/apps/production-control", ["production-control.access"]);

    await screen.findByRole("heading", { name: "Acesso não disponível" });
    expect(screen.queryByTestId("overview")).toBeNull();
  });
});
