import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

const envelope = (data: unknown) =>
  new Response(JSON.stringify({ success: true, message: "OK", data }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

function renderApp(pathname: string, permissions: string[], isSuperadmin = false) {
  window.history.pushState({}, "", pathname);
  return render(
    <App permissions={permissions} isSuperadmin={isSuperadmin} getAccessToken={() => "token"} />,
  );
}

describe("Delpi MES App — registrations area", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => Promise.resolve(envelope({ items: [] }))),
    );
  });
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows Cadastros only to users with the manage permission", async () => {
    renderApp("/apps/delpi-mes/registrations", [
      "delpi-mes.access",
      "delpi-mes.downtime-reasons.manage",
    ]);
    await screen.findByRole("heading", { name: "Cadastros" });
    expect(screen.getAllByText("Cadastro global").length).toBeGreaterThan(0);
    expect(screen.getByText("As alterações são válidas para todas as filiais.")).toBeTruthy();
    expect(screen.getByText("Motivos de parada")).toBeTruthy();
    expect(screen.queryByText("Filial")).toBeNull();
  });

  it("shows Cadastros to a human superadmin", async () => {
    renderApp("/apps/delpi-mes/registrations", [], true);
    await screen.findByRole("heading", { name: "Cadastros" });
  });

  it("hides Cadastros without the manage permission", async () => {
    renderApp("/apps/delpi-mes/registrations", [
      "delpi-mes.access",
      "delpi-mes.monitoring.view",
      "delpi-mes.view.filial-01",
    ]);
    await screen.findByRole("heading", { name: "Acesso não disponível" });
    expect(
      screen.getByText("Seu perfil não possui permissão para administrar os cadastros do Delpi MES."),
    ).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Cadastros" })).toBeNull();
    expect(screen.queryByText("Motivos de parada")).toBeNull();
  });

  it("renders the global catalog area without any branch permission", async () => {
    renderApp("/apps/delpi-mes/registrations/downtime-reasons", [
      "delpi-mes.access",
      "delpi-mes.downtime-reasons.manage",
    ]);
    await screen.findByRole("heading", { name: "Motivos de parada" });
    expect(screen.queryByRole("heading", { name: "Acesso não disponível" })).toBeNull();
    expect(screen.queryByText("Filial")).toBeNull();
  });

  it("keeps branch-scoped areas forbidden without a branch permission", async () => {
    renderApp("/apps/delpi-mes/monitoring", ["delpi-mes.access", "delpi-mes.monitoring.view"]);
    await screen.findByRole("heading", { name: "Acesso não disponível" });
  });

  it("does not pull another plugin back to the MES canonical url", async () => {
    window.history.pushState({}, "", "/apps/production-control/machine-load?branch=02");
    render(
      <App
        pathname="/apps/delpi-mes/monitoring"
        permissions={[
          "delpi-mes.access",
          "delpi-mes.monitoring.view",
          "delpi-mes.view.filial-01",
          "delpi-mes.view.filial-02",
        ]}
        getAccessToken={() => "token"}
      />,
    );
    await screen.findByRole("heading", { name: "Delpi MES" });
    expect(window.location.pathname).toBe("/apps/production-control/machine-load");
    expect(window.location.search).toBe("?branch=02");
  });

  it("still canonicalizes a MES url that is missing the branch", async () => {
    renderApp("/apps/delpi-mes/monitoring", [
      "delpi-mes.access",
      "delpi-mes.monitoring.view",
      "delpi-mes.view.filial-01",
    ]);
    await screen.findByRole("heading", { name: "Delpi MES" });
    await waitFor(() => {
      expect(window.location.pathname).toBe("/apps/delpi-mes/monitoring");
      expect(window.location.search).toBe("?branch=01");
    });
  });

  it("navigates from the hub to the downtime-reasons catalog", async () => {
    renderApp("/apps/delpi-mes/registrations", [
      "delpi-mes.access",
      "delpi-mes.downtime-reasons.manage",
    ]);
    await screen.findByRole("heading", { name: "Cadastros" });
    fireEvent.click(screen.getByText("Motivos de parada"));
    await screen.findByRole("heading", { name: "Motivos de parada" });
    expect(window.location.pathname).toBe("/apps/delpi-mes/registrations/downtime-reasons");
  });
});
