import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ServerWindowsServicesSection } from "./ServerWindowsServicesSection";
import { mockApi, requestedPaths } from "../../test/harness";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><ServerWindowsServicesSection serverId="dc7da8d3-b7d6-48b2-83ad-619b481f2183" /></QueryClientProvider>);
}

describe("Windows SCM read-only services inventory", () => {
  it("lists collected services without any control buttons", async () => {
    const fetchMock = mockApi({
      "/servers/dc7da8d3-b7d6-48b2-83ad-619b481f2183/host-services": {
        data: {
          items: [
            { name: "REST$PROD", display_name: "REST de apontamento",
              description: "API", state: "running", start_mode: "auto",
              can_stop: true, is_present: true, observed_at: "2026-11-12T10:00:00Z",
              updated_at: "2026-11-12T10:00:00Z" },
          ],
          total: 1, page: 1, page_size: 25,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z",
            service_count: 1 },
        },
      },
    });
    setup();
    expect(await screen.findByText("REST de apontamento")).toBeTruthy();
    expect(screen.getByText("REST$PROD")).toBeTruthy();
    expect(screen.getByText("Em execução")).toBeTruthy();
    expect(screen.getByText("Automático")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /reiniciar|parar|iniciar/i })).toBeNull();
    fireEvent.change(screen.getByRole("searchbox", { name: "Pesquisar serviço Windows" }),
      { target: { value: "REST" } });
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) =>
      new URL(String(input), "http://localhost").searchParams.get("q") === "REST"
    )).toBe(true));
    expect(requestedPaths(fetchMock).every((path) => path.endsWith("/host-services"))).toBe(true);
  });

  it("distinguishes no completed collection from an empty result", async () => {
    mockApi({
      "/servers/dc7da8d3-b7d6-48b2-83ad-619b481f2183/host-services": {
        data: { items: [], total: 0, page: 1, page_size: 25, current: null },
      },
    });
    setup();
    expect(await screen.findByText(/Nenhuma coleta completa recebida/)).toBeTruthy();
    expect(screen.getByText(/Nenhum serviço encontrado para os filtros/)).toBeTruthy();
  });
});
