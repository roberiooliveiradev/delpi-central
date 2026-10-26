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

const EMPTY_ANALYTICS = {
  branch: "01",
  from: "2026-02-01T03:00:00.000Z",
  to: "2026-02-10T12:00:00.000Z",
  referenceAt: "2026-02-10T12:00:00.000Z",
  timezone: "America/Sao_Paulo",
  appliedFilters: {},
  summary: {
    totalStoppedSeconds: 0,
    attributedSeconds: 0,
    occurrencesCount: 0,
    averageOccurrenceSeconds: 0,
    pendingCount: 0,
    openCount: 0,
  },
  byReason: [],
  byWorkCenter: [],
  byDay: [],
  byWeekdayHour: [],
  quality: { overlapDetected: false, overlapSeconds: 0, partial: false, factsCapped: false },
};

describe("Delpi MES App — downtimes area", () => {
  let fetchMock: ReturnType<typeof vi.fn>;
  beforeEach(() => {
    fetchMock = vi.fn().mockImplementation((url: string) =>
      Promise.resolve(
        envelope(
          url.includes("/downtimes/analytics")
            ? EMPTY_ANALYTICS
            : { items: [], total: 0, page: 1, pageSize: 50 },
        ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the Paradas page for authorized users instead of the placeholder", async () => {
    renderApp("/apps/delpi-mes/downtimes", [
      "delpi-mes.access",
      "delpi-mes.downtimes.view",
      "delpi-mes.view.filial-01",
    ]);
    await screen.findByRole("heading", { name: "Paradas" });
    await screen.findByText("Nenhuma parada registrada no período");
    expect(screen.queryByText(/está em preparação|em breve/i)).toBeNull();
    const urls = fetchMock.mock.calls.map(([url]) => url as string);
    expect(urls.some((url) => url.includes("/downtimes?"))).toBe(true);
    expect(urls.some((url) => url.includes("/downtimes/filter-options"))).toBe(true);
  });

  it("preserves the downtimes filters in the canonical URL", async () => {
    window.history.pushState(
      {},
      "",
      "/apps/delpi-mes/downtimes?branch=01&reasonCode=SETUP&page=2",
    );
    render(
      <App
        permissions={[
          "delpi-mes.access",
          "delpi-mes.downtimes.view",
          "delpi-mes.view.filial-01",
        ]}
        getAccessToken={() => "token"}
      />,
    );
    await screen.findByRole("heading", { name: "Paradas" });
    await waitFor(() => {
      expect(window.location.pathname).toBe("/apps/delpi-mes/downtimes");
      expect(window.location.search).toContain("reasonCode=SETUP");
      expect(window.location.search).toContain("page=2");
    });
  });

  it("denies an explicit downtimes route without the area permission", async () => {
    renderApp("/apps/delpi-mes/downtimes", [
      "delpi-mes.access",
      "delpi-mes.monitoring.view",
      "delpi-mes.view.filial-01",
    ]);
    // recusa explicita — sem redirecionamento silencioso para outra area
    await screen.findByRole("heading", { name: "Acesso não disponível" });
    expect(
      screen.getByText("Seu perfil não possui permissão para acessar esta área do Delpi MES."),
    ).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Paradas" })).toBeNull();
    expect(window.location.pathname).toBe("/apps/delpi-mes/downtimes");
    // nenhuma consulta de paradas — e a area nao chega a montar outra pagina
    const urls = fetchMock.mock.calls.map(([url]) => url as string);
    expect(urls.some((url) => url.includes("/downtimes"))).toBe(false);
    expect(urls).toEqual([]);
  });

  it("still redirects the product root to the first permitted area", async () => {
    renderApp("/apps/delpi-mes", [
      "delpi-mes.access",
      "delpi-mes.monitoring.view",
      "delpi-mes.view.filial-01",
    ]);
    await waitFor(() => {
      expect(window.location.pathname).toBe("/apps/delpi-mes/monitoring");
      expect(window.location.search).toContain("branch=01");
    });
    expect(screen.queryByRole("heading", { name: "Acesso não disponível" })).toBeNull();
  });

  it("still redirects the root to Paradas when it is the only permitted area", async () => {
    renderApp("/apps/delpi-mes", [
      "delpi-mes.access",
      "delpi-mes.downtimes.view",
      "delpi-mes.view.filial-01",
    ]);
    await waitFor(() => {
      expect(window.location.pathname).toBe("/apps/delpi-mes/downtimes");
      expect(window.location.search).toContain("branch=01");
    });
    expect(screen.queryByRole("heading", { name: "Acesso não disponível" })).toBeNull();
  });
});
