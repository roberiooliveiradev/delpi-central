import { cleanup, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Capabilities, Dashboard, Server } from "./api/itPortalApi";
import { mockApi, renderAt, requestedPaths } from "./test/harness";

const SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f";

const ALL_CAPS: Capabilities = {
  display_name: "Ana Souza",
  can_view_servers: true,
  can_manage_servers: true,
  can_create_notes: true,
  can_view_action_plans: true,
  can_manage_action_plans: true,
  can_view_services: false,
  can_manage_services: false,
  can_view_databases: false,
  can_manage_databases: false,
  can_view_networks: false,
  can_manage_networks: false,
  can_view_integrations: false,
  can_manage_integrations: false,
};

const VIEW_ONLY: Capabilities = {
  ...ALL_CAPS,
  can_manage_servers: false,
  can_create_notes: false,
  can_manage_action_plans: false,
};

function server(overrides: Partial<Server> = {}): Server {
  return {
    id: SERVER_ID,
    code: "SRV-0001",
    name: "ERP Produção",
    hostname: "srv-erp01.delpi.local",
    ip_address: "10.0.0.10",
    unit_code: "01",
    location: "Datacenter SC",
    environment: "production",
    server_type: "virtual",
    purpose: "ERP",
    operating_system: "Windows Server 2022",
    criticality: "critical",
    administrative_status: "in_operation",
    responsible: "Equipe Infra",
    description: null,
    revision: 1,
    archived: false,
    archived_at: null,
    archived_by_name: null,
    open_action_count: 0,
    created_at: "2026-11-01T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-02T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

function dashboard(overrides: Partial<Dashboard> = {}): Dashboard {
  return {
    reference_date: "2026-11-10",
    generated_at: "2026-11-10T12:00:00Z",
    servers: { total: 0, high_or_critical: 0 },
    recent_servers: [],
    action_plans: { open: 0, overdue: 0 },
    attention_action_plans: [],
    ...overrides,
  };
}

beforeEach(() => {
  vi.spyOn(console, "error").mockImplementation(() => undefined);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("portal access", () => {
  it("shows forbidden state when the BFF denies portal access", async () => {
    mockApi({ "/me/capabilities": { status: 403, body: { detail: "Forbidden" } } });
    renderAt("/apps/it-portal");
    expect(await screen.findByText(/não tem acesso ao Portal de TI/i)).toBeTruthy();
  });

  it("shows unavailable state when authorization cannot be resolved", async () => {
    mockApi({ "/me/capabilities": { status: 503, body: { detail: "Service Unavailable" } } });
    renderAt("/apps/it-portal");
    expect(await screen.findByText("Serviço indisponível")).toBeTruthy();
  });

  it("blocks the servers page without servers.view", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: { ...ALL_CAPS, can_view_servers: false, can_view_action_plans: false } },
    });
    renderAt("/apps/it-portal/servers");
    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes("/servers"))).toBe(false);
  });

  it("does not render unknown areas as pages", async () => {
    mockApi({ "/me/capabilities": { data: ALL_CAPS } });
    renderAt("/apps/it-portal/monitoring");
    expect(await screen.findByText("Página não encontrada")).toBeTruthy();
  });
});

describe("home", () => {
  it("offers to register the first server when inventory is empty", async () => {
    mockApi({ "/me/capabilities": { data: ALL_CAPS }, "/dashboard": { data: dashboard() } });
    renderAt("/apps/it-portal");
    expect(await screen.findByText("Nenhum servidor cadastrado")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Cadastrar servidor/ })).toBeTruthy();
  });

  it("hides the register CTA without servers.manage", async () => {
    mockApi({ "/me/capabilities": { data: VIEW_ONLY }, "/dashboard": { data: dashboard() } });
    renderAt("/apps/it-portal");
    expect(await screen.findByText("Nenhum servidor cadastrado")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Cadastrar servidor/ })).toBeNull();
  });

  it("renders KPIs from the API and omits action KPIs without actions.view", async () => {
    mockApi({
      "/me/capabilities": { data: { ...VIEW_ONLY, can_view_action_plans: false } },
      "/dashboard": {
        data: dashboard({
          servers: { total: 3, high_or_critical: 2 },
          recent_servers: [server()],
          action_plans: null,
          attention_action_plans: null,
        }),
      },
    });
    renderAt("/apps/it-portal");
    const indicators = await screen.findByRole("group", { name: "Indicadores" });
    expect(within(indicators).getByText("3")).toBeTruthy();
    expect(within(indicators).getByText("2")).toBeTruthy();
    expect(within(indicators).queryByText("Ações atrasadas")).toBeNull();
    expect(screen.getByText("ERP Produção")).toBeTruthy();
  });
});

describe("servers", () => {
  it("lists servers from the BFF and hides management without permission", async () => {
    mockApi({
      "/me/capabilities": { data: VIEW_ONLY },
      "/servers": { data: { items: [server()], total: 1, page: 1, page_size: 20 } },
    });
    renderAt("/apps/it-portal/servers");
    expect(await screen.findByText("srv-erp01.delpi.local")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Cadastrar servidor/ })).toBeNull();
  });

  it("shows the secret warning on the note composer", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: ALL_CAPS },
      [`/servers/${SERVER_ID}`]: { data: server() },
      [`/servers/${SERVER_ID}/notes`]: { data: [] },
      [`/servers/${SERVER_ID}/history`]: { data: [] },
      [`/servers/${SERVER_ID}/observations/latest`]: { data: null },
      "/action-plans": { data: { items: [], total: 0, page: 1, page_size: 20 } },
    });
    renderAt(`/apps/it-portal/servers/${SERVER_ID}`);
    expect(await screen.findByRole("note")).toBeTruthy();
    expect(screen.getByText(/Não registre senhas/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Arquivar/ })).toBeTruthy();
    // Etapa 1 preservada: sem permissões E2A não há seções nem chamadas de inventário novas.
    expect(screen.queryByText("Componentes vinculados")).toBeNull();
    expect(screen.queryByText("Serviços hospedados")).toBeNull();
    const paths = requestedPaths(fetchMock);
    expect(paths.some((p) => p.includes("service-hostings") || p.startsWith("/database-instances"))).toBe(false);
  });

  it("makes archived servers read-only", async () => {
    mockApi({
      "/me/capabilities": { data: ALL_CAPS },
      [`/servers/${SERVER_ID}`]: {
        data: server({ archived: true, archived_at: "2026-11-05T10:00:00Z", archived_by_name: "Ana Souza" }),
      },
      [`/servers/${SERVER_ID}/notes`]: { data: [] },
      [`/servers/${SERVER_ID}/history`]: { data: [] },
      [`/servers/${SERVER_ID}/observations/latest`]: { data: null },
      "/action-plans": { data: { items: [], total: 0, page: 1, page_size: 20 } },
    });
    renderAt(`/apps/it-portal/servers/${SERVER_ID}`);
    expect(await screen.findByRole("button", { name: /Restaurar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Editar/ })).toBeNull();
    expect(screen.queryByRole("note")).toBeNull();
    expect(screen.queryByRole("button", { name: /Novo plano/ })).toBeNull();
  });

  it("shows backend field errors when creating a server", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: ALL_CAPS },
      "/servers": { data: { items: [], total: 0, page: 1, page_size: 20 } },
      "POST /servers": {
        status: 422,
        body: {
          success: false,
          message: "Dados inválidos.",
          data: { error: { code: "invalid_request", details: { fields: { hostname: "Hostname inválido." } } } },
        },
      },
    });
    renderAt("/apps/it-portal/servers");
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar servidor/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Cadastrar" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Dados inválidos.")).toBeTruthy();
    expect(within(alert).getByText(/Hostname inválido/)).toBeTruthy();
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(post).toBeTruthy();
  });

  it("offers only valid status transitions for an action plan", async () => {
    mockApi({
      "/me/capabilities": { data: ALL_CAPS },
      "/action-plans": {
        data: {
          items: [
            {
              id: "9a1b2c3d-0000-4000-8000-000000000001",
              code: "PA-0001",
              server_id: SERVER_ID,
              server: {
                id: SERVER_ID,
                code: "SRV-0001",
                name: "ERP Produção",
                hostname: "srv-erp01",
                environment: "production",
                unit_code: "01",
                archived: false,
              },
              title: "Aplicar patch",
              description: null,
              responsible: null,
              priority: "high",
              status: "done",
              due_date: "2026-11-01",
              completed_at: "2026-11-02T10:00:00Z",
              is_overdue: false,
              revision: 3,
              created_at: "2026-11-01T10:00:00Z",
              created_by_name: "Ana Souza",
              updated_at: "2026-11-02T10:00:00Z",
              updated_by_name: "Ana Souza",
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
      },
    });
    renderAt("/apps/it-portal/action-plans");
    fireEvent.click(await screen.findByRole("button", { name: "Alterar status de PA-0001" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Status atual: Concluído/)).toBeTruthy();
    expect(within(dialog).getAllByText("Em andamento").length).toBeGreaterThan(0);
    expect(within(dialog).queryByText("Cancelado")).toBeNull();
  });

  it("shows not found for a missing server", async () => {
    mockApi({
      "/me/capabilities": { data: ALL_CAPS },
      [`/servers/${SERVER_ID}`]: { status: 404, body: { success: false, message: "Servidor não encontrado.", data: null } },
    });
    renderAt(`/apps/it-portal/servers/${SERVER_ID}`);
    expect(await screen.findByText("Servidor não encontrado.")).toBeTruthy();
  });
});
