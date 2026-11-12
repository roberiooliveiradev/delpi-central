import { render, screen, fireEvent, waitFor, cleanup, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ServerWindowsServicesSection } from "./ServerWindowsServicesSection";
import { mockApi, requestedPaths, requestBodies } from "../../test/harness";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function setup(canManageFavorites = false, canControlServices = false) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={client}><ServerWindowsServicesSection serverId="dc7da8d3-b7d6-48b2-83ad-619b481f2183" canManageFavorites={canManageFavorites} canControlServices={canControlServices} /></QueryClientProvider>);
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
    expect(within(screen.getByRole("table", { name: "Inventário de serviços do Windows" })).getByText("Em execução")).toBeTruthy();
    expect(within(screen.getByRole("table", { name: "Inventário de serviços do Windows" })).getByText("Automático")).toBeTruthy();
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
    expect(screen.getByText("Nenhum serviço encontrado")).toBeTruthy();
    expect(screen.getByText(/Aguardando o primeiro inventário completo/)).toBeTruthy();
  });


  it("shows server-wide totals, compact rows and expandable details", async () => {
    mockApi({
      "/servers/dc7da8d3-b7d6-48b2-83ad-619b481f2183/host-services": {
        data: {
          items: [{
            name: "REST$PROD", display_name: "REST de apontamento",
            description: "Serviço responsável pela comunicação com a produção.",
            state: "running", start_mode: "auto", can_stop: true, is_present: true,
            observed_at: "2026-11-12T10:00:00Z", updated_at: "2026-11-12T10:00:00Z",
          }],
          total: 263, page: 1, page_size: 25,
          current: {
            run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z",
            received_at: "2026-11-12T10:00:00Z",
            service_count: 263,
          },
        },
      },
    });
    setup();
    expect(await screen.findByText("REST de apontamento")).toBeTruthy();
    expect(screen.getAllByText("263").length).toBeGreaterThan(0);
    expect(screen.getByText("263 resultado(s)")).toBeTruthy();
    const details = screen.getByRole("button", { name: "Ver detalhes de REST de apontamento" });
    expect(details.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(details);
    expect(screen.getByText("Serviço responsável pela comunicação com a produção.")).toBeTruthy();
    const collapse = screen.getByRole("button", { name: "Ocultar detalhes de REST de apontamento" });
    expect(collapse.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(collapse);
    expect(screen.queryByText("Serviço responsável pela comunicação com a produção.")).toBeNull();
    expect(screen.queryByRole("button", { name: /reiniciar|parar serviço|iniciar serviço/i })).toBeNull();
  });

  it("uses API pagination and filters, with a safe reset", async () => {
    const fetchMock = mockApi({
      "/servers/dc7da8d3-b7d6-48b2-83ad-619b481f2183/host-services": {
        data: {
          items: [{ name: "X", display_name: "Servico X", description: null,
            state: "stopped", start_mode: "manual", can_stop: false,
            is_present: true, observed_at: "2026-11-12T10:00:00Z",
            updated_at: "2026-11-12T10:00:00Z" }],
          total: 32, page: 1, page_size: 25,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z", service_count: 32 },
        },
      },
    });
    setup();
    expect(await screen.findByText("Servico X")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Próxima página" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) =>
      new URL(String(input), "http://localhost").searchParams.get("page") === "2"
    )).toBe(true));

    fireEvent.change(screen.getByRole("combobox", { name: "Estado do serviço" }),
      { target: { value: "stopped" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Modo de inicialização" }),
      { target: { value: "manual" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Presença no inventário" }),
      { target: { value: "no" } });
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) => {
      const params = new URL(String(input), "http://localhost").searchParams;
      return params.get("state") === "stopped" && params.get("start_mode") === "manual" &&
        params.get("present") === "no" && params.get("page") === "1";
    })).toBe(true));

    fireEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));
    expect((screen.getByRole("combobox", { name: "Estado do serviço" }) as HTMLSelectElement).value).toBe("");
    expect((screen.getByRole("combobox", { name: "Presença no inventário" }) as HTMLSelectElement).value).toBe("yes");
    expect(fetchMock.mock.calls.every(([, init]) => !init?.method || init.method === "GET")).toBe(true);
  });

  it("keeps favorites precise and server-side with a one-click star", async () => {
    const id = "dc7da8d3-b7d6-48b2-83ad-619b481f2183";
    const fetchMock = mockApi({
      ["/servers/" + id + "/host-services"]: {
        data: {
          items: [{
            service_key: "rest$prod", name: "REST$PROD", display_name: "REST de apontamento",
            description: "API", state: "running", start_mode: "auto", is_present: true,
            is_favorite: false, criticality: "normal", can_stop: true,
            observed_at: "2026-11-12T10:00:00Z", updated_at: "2026-11-12T10:00:00Z",
          }],
          favorites_count: 0, total: 1, page: 1, page_size: 25,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z", service_count: 1 },
        },
      },
      ["PUT /servers/" + id + "/host-services/rest%24prod/preferences"]: {
        data: { service_key: "rest$prod", is_favorite: true, criticality: "normal" },
      },
    });
    setup(true);
    expect(await screen.findByText("REST de apontamento")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Adicionar REST de apontamento aos favoritos" }).getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(screen.getByRole("button", { name: "Adicionar REST de apontamento aos favoritos" }));
    await waitFor(() => expect(requestBodies(fetchMock, "PUT")).toEqual([
      { is_favorite: true, criticality: "normal" },
    ]));
    fireEvent.click(screen.getByRole("button", { name: /Favoritos/ }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([input]) =>
      new URL(String(input), "http://localhost").searchParams.get("favorites_only") === "true" &&
      new URL(String(input), "http://localhost").searchParams.get("present") === "all"
    )).toBe(true));
    expect(screen.queryByRole("button", { name: /reiniciar|parar serviço|iniciar serviço/i })).toBeNull();
  });

  it("shows criticality as a discreet accent and keeps the editor inside details", async () => {
    const id = "dc7da8d3-b7d6-48b2-83ad-619b481f2183";
    const fetchMock = mockApi({
      ["/servers/" + id + "/host-services"]: {
        data: {
          items: [{
            service_key: "rest$prod", name: "REST$PROD", display_name: "REST de apontamento",
            description: "API", state: "running", start_mode: "auto", is_present: true,
            is_favorite: true, criticality: "high", can_stop: true,
            observed_at: "2026-11-12T10:00:00Z", updated_at: "2026-11-12T10:00:00Z",
          }],
          favorites_count: 1, total: 1, page: 1, page_size: 25,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z", service_count: 1 },
        },
      },
      ["PUT /servers/" + id + "/host-services/rest%24prod/preferences"]: {
        data: { service_key: "rest$prod", is_favorite: true, criticality: "critical" },
      },
    });
    setup(true);
    expect(await screen.findByText("REST de apontamento")).toBeTruthy();
    expect(screen.getByText("Alta")).toBeTruthy();
    expect(screen.queryByRole("combobox", { name: "Criticidade de REST de apontamento" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes de REST de apontamento" }));
    fireEvent.change(screen.getByRole("combobox", { name: "Criticidade de REST de apontamento" }),
      { target: { value: "critical" } });
    await waitFor(() => expect(requestBodies(fetchMock, "PUT")).toContainEqual({
      is_favorite: true, criticality: "critical",
    }));
  });


  it("keeps controls invisible to viewers and blocked services", async () => {
    mockApi({
      "/servers/dc7da8d3-b7d6-48b2-83ad-619b481f2183/host-services": {
        data: {
          items: [{
            service_key: "test_delpi", name: "TEST_DELPI", display_name: "Serviço de teste",
            description: "Ambiente isolado", state: "running", start_mode: "auto",
            can_stop: true, is_present: true, is_favorite: false,
            criticality: "normal", control_allowed: true,
            observed_at: "2026-11-12T10:00:00Z", updated_at: "2026-11-12T10:00:00Z",
          }],
          total: 1, page: 1, page_size: 25, favorites_count: 0,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z", service_count: 1 },
        },
      },
    });
    setup(false, false);
    expect(await screen.findByText("Serviço de teste")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes de Serviço de teste" }));
    expect(screen.queryByRole("button", { name: "Reiniciar" })).toBeNull();
    expect(screen.queryByText("Controle remoto")).toBeNull();
  });

  it("asks confirmation and shows only a Windows-verified result", async () => {
    const id = "dc7da8d3-b7d6-48b2-83ad-619b481f2183";
    const actionId = "22222222-2222-4222-8222-222222222222";
    Object.defineProperty(globalThis.crypto, "randomUUID", {
      configurable: true, value: () => "33333333-3333-4333-8333-333333333333",
    });
    const fetchMock = mockApi({
      ["/servers/" + id + "/host-services"]: {
        data: {
          items: [{
            service_key: "test_delpi", name: "TEST_DELPI", display_name: "Serviço de teste",
            description: "Ambiente isolado", state: "running", start_mode: "auto",
            can_stop: true, is_present: true, is_favorite: false,
            criticality: "normal", control_allowed: true,
            observed_at: "2026-11-12T10:00:00Z", updated_at: "2026-11-12T10:00:00Z",
          }],
          total: 1, page: 1, page_size: 25, favorites_count: 0,
          current: { run_id: "11111111-1111-4111-8111-111111111111",
            observed_at: "2026-11-12T10:00:00Z", received_at: "2026-11-12T10:00:00Z", service_count: 1 },
        },
      },
      ["POST /servers/" + id + "/host-services/test_delpi/actions"]: {
        status: 202,
        data: { id: actionId, server_id: id, service_name: "TEST_DELPI",
          service_key: "test_delpi", action: "restart", state_before: "running",
          status: "queued", state_after: null, error_code: null, requested_at: "2026-11-12T10:00:00Z",
          claimed_at: null, finished_at: null, requested_by_name: "TI" },
      },
      ["/servers/" + id + "/host-services/actions/" + actionId]: {
        data: { id: actionId, server_id: id, service_name: "TEST_DELPI",
          service_key: "test_delpi", action: "restart", state_before: "running",
          status: "succeeded", state_after: "running", error_code: null,
          requested_at: "2026-11-12T10:00:00Z", claimed_at: "2026-11-12T10:00:01Z",
          finished_at: "2026-11-12T10:00:03Z", requested_by_name: "TI" },
      },
    });
    setup(false, true);
    expect(await screen.findByText("Serviço de teste")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Reiniciar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes de Serviço de teste" }));
    fireEvent.click(screen.getByRole("button", { name: "Reiniciar" }));
    expect(requestBodies(fetchMock, "POST")).toEqual([]);
    expect(screen.getByText(/pode interromper sistemas e usuários/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar ação" }));
    await waitFor(() => expect(requestBodies(fetchMock, "POST")).toContainEqual({
      action: "restart", request_id: "33333333-3333-4333-8333-333333333333",
      confirmed: true,
    }));
    expect(await screen.findByText(/Concluído e confirmado pelo Windows/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Iniciar serviço no Windows sem confirmação/ })).toBeNull();
  });

});
