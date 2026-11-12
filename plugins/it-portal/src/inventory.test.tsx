import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  Capabilities,
  DatabaseConsumer,
  DatabaseInstance,
  Server,
  Service,
  ServiceHosting,
} from "./api/itPortalApi";
import { mockApi, renderAt, requestedPaths } from "./test/harness";

const SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f";
const SERVICE_ID = "7c1d2e3f-4a5b-4c6d-8e9f-0a1b2c3d4e5f";
const DATABASE_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d";
const HOSTING_ID = "9f8e7d6c-5b4a-4c3d-8e2f-1a0b9c8d7e6f";

const E1_ONLY: Capabilities = {
  display_name: "Ana Souza",
  can_view_servers: true,
  can_manage_servers: true,
  can_create_notes: true,
  can_view_action_plans: false,
  can_manage_action_plans: false,
  can_view_services: false,
  can_manage_services: false,
  can_view_databases: false,
  can_manage_databases: false,
  can_view_networks: false,
  can_manage_networks: false,
  can_view_integrations: false,
  can_manage_integrations: false,
};

const INVENTORY_MANAGER: Capabilities = {
  ...E1_ONLY,
  can_view_services: true,
  can_manage_services: true,
  can_view_databases: true,
  can_manage_databases: true,
};

const INVENTORY_VIEWER: Capabilities = {
  ...INVENTORY_MANAGER,
  can_manage_servers: false,
  can_create_notes: false,
  can_manage_services: false,
  can_manage_databases: false,
};

const SERVER_SUMMARY = {
  id: SERVER_ID,
  code: "SRV-0001",
  name: "ERP Produção",
  hostname: "srv-erp01.delpi.local",
  environment: "production" as const,
  unit_code: "01" as const,
  archived: false,
};

function server(overrides: Partial<Server> = {}): Server {
  return {
    ...SERVER_SUMMARY,
    ip_address: null,
    location: null,
    server_type: "virtual",
    purpose: null,
    operating_system: null,
    criticality: "critical",
    administrative_status: "in_operation",
    responsible: "Equipe Infra",
    description: null,
    revision: 1,
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

function service(overrides: Partial<Service> = {}): Service {
  return {
    id: SERVICE_ID,
    code: "SVC-0001",
    name: "Portal Interno",
    description: null,
    service_kind: "business_application",
    service_type: "web_application",
    technology: "Python/FastAPI",
    environment: "production",
    unit_code: "01",
    port: 8443,
    criticality: "high",
    responsible: "Equipe Sistemas",
    administrative_status: "in_operation",
    revision: 1,
    archived: false,
    archived_at: null,
    archived_by_name: null,
    hosting_count: 1,
    database_count: 1,
    created_at: "2026-11-03T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-03T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

const SERVICE_SUMMARY = {
  id: SERVICE_ID,
  code: "SVC-0001",
  name: "Portal Interno",
  service_kind: "business_application" as const,
  environment: "production" as const,
  criticality: "high" as const,
  archived: false,
};

function database(overrides: Partial<DatabaseInstance> = {}): DatabaseInstance {
  return {
    id: DATABASE_ID,
    code: "DB-0001",
    name: "ERP_PROD",
    dbms: "sql_server",
    version: "2019",
    server_id: SERVER_ID,
    server: SERVER_SUMMARY,
    port: 1433,
    environment: "production",
    purpose: "ERP",
    criticality: "critical",
    responsible: "Equipe Infra",
    administrative_status: "in_operation",
    technical_notes: null,
    revision: 1,
    archived: false,
    archived_at: null,
    archived_by_name: null,
    consumer_count: 1,
    created_at: "2026-11-03T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-03T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

const HOSTING: ServiceHosting = {
  id: HOSTING_ID,
  service_id: SERVICE_ID,
  server_id: SERVER_ID,
  runtime: "container",
  instance_name: "portal-api",
  notes: null,
  created_at: "2026-11-04T12:00:00Z",
  created_by_name: "Ana Souza",
  service: SERVICE_SUMMARY,
  server: SERVER_SUMMARY,
};

const CONSUMER: DatabaseConsumer = {
  id: "5d4c3b2a-1f0e-4d9c-8b7a-6f5e4d3c2b1a",
  database_instance_id: DATABASE_ID,
  service_id: SERVICE_ID,
  notes: "Leitura e escrita",
  created_at: "2026-11-04T12:00:00Z",
  created_by_name: "Ana Souza",
  database: {
    id: DATABASE_ID,
    code: "DB-0001",
    name: "ERP_PROD",
    dbms: "sql_server",
    environment: "production",
    criticality: "critical",
    archived: false,
  },
  service: SERVICE_SUMMARY,
};

const page = <T,>(items: T[]) => ({ data: { items, total: items.length, page: 1, page_size: 20 } });

function serverDetailRoutes(caps: Capabilities) {
  return {
    "/me/capabilities": { data: caps },
    [`/servers/${SERVER_ID}`]: { data: server() },
    [`/servers/${SERVER_ID}/notes`]: { data: [] },
    [`/servers/${SERVER_ID}/history`]: { data: [] },
    [`/servers/${SERVER_ID}/observations/latest`]: { data: null },
    [`/servers/${SERVER_ID}/service-hostings`]: { data: [HOSTING] },
    "/database-instances": page([database()]),
    [`DELETE /service-hostings/${HOSTING_ID}`]: { data: { id: HOSTING_ID } },
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

describe("inventory navigation and access", () => {
  it("adds Serviços and Bancos de dados to the nav only with view capabilities", async () => {
    mockApi({ "/me/capabilities": { data: INVENTORY_VIEWER } });
    renderAt("/apps/it-portal/help");
    const nav = await screen.findByRole("navigation", { name: "Navegação do Portal de TI" });
    expect(within(nav).getAllByText("Serviços").length).toBeGreaterThan(0);
    expect(within(nav).getAllByText("Bancos de dados").length).toBeGreaterThan(0);
  });

  it("keeps the Etapa 1 nav for users without inventory permissions", async () => {
    mockApi({ "/me/capabilities": { data: E1_ONLY } });
    renderAt("/apps/it-portal/help");
    const nav = await screen.findByRole("navigation", { name: "Navegação do Portal de TI" });
    expect(within(nav).getAllByText("Servidores").length).toBeGreaterThan(0);
    expect(within(nav).queryByText("Serviços")).toBeNull();
    expect(within(nav).queryByText("Bancos de dados")).toBeNull();
  });

  it.each([
    ["/apps/it-portal/services", "/services"],
    [`/apps/it-portal/services/${SERVICE_ID}`, "/services"],
    ["/apps/it-portal/databases", "/database-instances"],
    [`/apps/it-portal/databases/${DATABASE_ID}`, "/database-instances"],
  ])("blocks %s without the view capability and never calls the API", async (path, apiPrefix) => {
    const fetchMock = mockApi({ "/me/capabilities": { data: E1_ONLY } });
    renderAt(path);
    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
    expect(requestedPaths(fetchMock).some((p) => p.startsWith(apiPrefix))).toBe(false);
  });
});

describe("help", () => {
  it("documents services, databases, links and the new permissions", async () => {
    mockApi({ "/me/capabilities": { data: E1_ONLY } });
    renderAt("/apps/it-portal/help");
    expect(await screen.findByRole("heading", { name: "Cadastrar serviços e aplicações" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Inventariar instâncias de bancos de dados" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Ligar serviços, servidores e bancos" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Ler o inventário automático do servidor" })).toBeTruthy();
    expect(screen.getAllByText("Gerenciar bancos de dados").length).toBeGreaterThan(0);
    expect(screen.getByText("Remover um vínculo apaga o serviço ou o servidor?")).toBeTruthy();
  });
});

describe("services", () => {
  it("lists services and hides management for viewers", async () => {
    mockApi({ "/me/capabilities": { data: INVENTORY_VIEWER }, "/services": page([service()]) });
    renderAt("/apps/it-portal/services");
    expect(await screen.findByText("Portal Interno")).toBeTruthy();
    expect(screen.getAllByText("Aplicação de negócio").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Cadastrar serviço/ })).toBeNull();
  });

  it("shows an actionable empty state for managers", async () => {
    mockApi({ "/me/capabilities": { data: INVENTORY_MANAGER }, "/services": page([]) });
    renderAt("/apps/it-portal/services");
    expect(await screen.findByText(/Nenhum serviço cadastrado. Use «Cadastrar serviço»/)).toBeTruthy();
  });

  it("shows backend field errors when creating a service", async () => {
    mockApi({
      "/me/capabilities": { data: INVENTORY_MANAGER },
      "/services": page([]),
      "POST /services": {
        status: 422,
        body: {
          success: false,
          message: "Revise os campos do serviço.",
          data: { error: { code: "invalid_service", details: { fields: { responsible: "Informe o responsável." } } } },
        },
      },
    });
    renderAt("/apps/it-portal/services");
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar serviço/ }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Não registre senhas, tokens ou credenciais/)).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cadastrar" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Revise os campos do serviço.")).toBeTruthy();
    expect(within(alert).getByText(/Informe o responsável/)).toBeTruthy();
  });

  it("renders service detail with hostings and databases; archived services are read-only", async () => {
    mockApi({
      "/me/capabilities": { data: INVENTORY_MANAGER },
      [`/services/${SERVICE_ID}`]: {
        data: service({ archived: true, archived_at: "2026-11-05T10:00:00Z", archived_by_name: "Ana Souza" }),
      },
      [`/services/${SERVICE_ID}/hostings`]: { data: [HOSTING] },
      [`/services/${SERVICE_ID}/database-instances`]: { data: [CONSUMER] },
      [`/services/${SERVICE_ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/services/${SERVICE_ID}`);
    expect(await screen.findByText("Servidores onde executa")).toBeTruthy();
    expect(await screen.findByText("ERP Produção")).toBeTruthy();
    expect(await screen.findByText("ERP_PROD")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Restaurar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Editar/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Vincular servidor/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Vincular banco/ })).toBeNull();
  });
});

describe("server detail — icon navigation and linked components", () => {
  it("opens one destination at a time and keeps data hidden until requested", async () => {
    const fetchMock = mockApi(serverDetailRoutes(INVENTORY_MANAGER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(await screen.findByText("Identificação")).toBeTruthy();
    expect(screen.queryByText("Serviços hospedados")).toBeNull();
    expect(screen.queryByText("Bancos de dados associados")).toBeNull();
    expect(requestedPaths(fetchMock).some((p) => p.includes("/service-hostings"))).toBe(false);

    fireEvent.click(within(navigation).getByRole("button", { name: /Serviços Aplicações hospedadas/ }));
    expect(await screen.findByText("Serviços vinculados")).toBeTruthy();
    expect(await screen.findByText("1 serviço ativo")).toBeTruthy();
    expect(await screen.findByText("Portal Interno")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Vincular serviço/ })).toBeTruthy();
    expect(screen.queryByText("Identificação")).toBeNull();
    expect(screen.queryByText("Bancos de dados associados")).toBeNull();

    fireEvent.click(within(navigation).getByRole("button", { name: /Bancos de dados/ }));
    expect(await screen.findByText("Bancos vinculados")).toBeTruthy();
    expect(await screen.findByText("1 instância ativa")).toBeTruthy();
    expect(await screen.findByText("ERP_PROD")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Cadastrar instância/ })).toBeTruthy();
    expect(screen.queryByText("Serviços hospedados")).toBeNull();
  });

  it("removes a service link after confirmation without deleting its underlying record", async () => {
    const fetchMock = mockApi(serverDetailRoutes(INVENTORY_MANAGER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /Serviços Aplicações hospedadas/ }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Remover vínculo entre Portal Interno e ERP Produção" }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Nenhum cadastro é excluído/)).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Remover vínculo" }));
    await waitFor(() => expect(requestedPaths(fetchMock, "DELETE")).toEqual(["/service-hostings/" + HOSTING_ID]));
    expect(requestedPaths(fetchMock, "DELETE").some((p) => p.startsWith("/services"))).toBe(false);
  });

  it("keeps viewing allowed but hides link management from read-only viewers", async () => {
    mockApi(serverDetailRoutes(INVENTORY_VIEWER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /Serviços Aplicações hospedadas/ }));
    expect(await screen.findByText("Portal Interno")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Vincular serviço/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Remover vínculo/ })).toBeNull();
    fireEvent.click(within(navigation).getByRole("button", { name: /Bancos de dados/ }));
    expect(await screen.findByText("ERP_PROD")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Cadastrar instância/ })).toBeNull();
  });

  it("does not show or request restricted destinations", async () => {
    const fetchMock = mockApi(
      serverDetailRoutes({ ...INVENTORY_VIEWER, can_view_services: false, can_manage_services: false }),
    );
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(within(navigation).queryByRole("button", { name: /Serviços Aplicações hospedadas/ })).toBeNull();
    fireEvent.click(within(navigation).getByRole("button", { name: /Bancos de dados/ }));
    expect(await screen.findByText("Bancos de dados associados")).toBeTruthy();
    expect(screen.queryByText("Serviços hospedados")).toBeNull();
    expect(requestedPaths(fetchMock).some((p) => p.includes("service-hostings"))).toBe(false);
  });

  it("shows automatic inventory empty state only after entering its destination", async () => {
    const fetchMock = mockApi(serverDetailRoutes(INVENTORY_VIEWER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(requestedPaths(fetchMock).some((p) => p.endsWith("/observations/latest"))).toBe(false);
    fireEvent.click(within(navigation).getByRole("button", { name: /Coleta automática/ }));
    expect(await screen.findByText(/Nenhuma observação automática registrada/)).toBeTruthy();
  });

  it("renders Linux telemetry and divergence with partial Docker state", async () => {
    const observation = {
      id: "obs-1",
      server_id: SERVER_ID,
      run_id: "run-test-0001",
      source: "linux_host_collector",
      collector_client_id: "it-portal-host-collector",
      observed_at: "2026-11-11T10:00:00Z",
      received_at: "2026-11-11T10:00:05Z",
      schema_version: "1",
      status: "partial",
      summary: {
        os: { name: "Ubuntu", version: "24.04", kernel: "6.8.0", architecture: "x86_64" },
        cpu_logical: 8,
        memory: { total_bytes: 16_000_000_000, available_bytes: 8_000_000_000 },
        host_nics: [{ name: "eth0", addresses: ["192.168.1.237/24"], state: "up" }],
        volumes: [{ mount_point: "/", size_bytes: 100, used_bytes: 40, used_percent: 40 }],
        systemd_services: [{ name: "docker.service", active_state: "active", sub_state: "running" }],
        docker_summary: { available: false, unavailable_reason: "no_permission" },
      },
      sections_status: { os: "ok", docker: "unavailable" },
      divergences: [
        { field: "operating_system", registered: "Windows Server 2022", observed: "Ubuntu 24.04" },
      ],
      created_at: "2026-11-11T10:00:05Z",
      presentation_status: "partial",
    };
    const fetchMock = mockApi({
      ...serverDetailRoutes(INVENTORY_VIEWER),
      ["/servers/" + SERVER_ID + "/observations/latest"]: { data: observation },
    });
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /Coleta automática/ }));
    await waitFor(() =>
      expect(requestedPaths(fetchMock).some((p) => p.endsWith("/observations/latest"))).toBe(true),
    );
    expect(await screen.findByRole("heading", { name: "Sistema e hardware" })).toBeTruthy();
    expect(screen.getByText("Parcial")).toBeTruthy();
    expect(screen.getByText("Diferenças em relação ao cadastro")).toBeTruthy();
    expect(screen.getByText(/Docker indisponível/)).toBeTruthy();
    expect(screen.getAllByText("8").length).toBeGreaterThan(0);
    expect(screen.getByText("CPUs lógicas · uso não coletado")).toBeTruthy();
  });

  it("renders only allowed destinations for a basic server user", async () => {
    mockApi(serverDetailRoutes(E1_ONLY));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(within(navigation).getByRole("button", { name: /Visão geral/ }).getAttribute("aria-pressed")).toBe("true");
    expect(within(navigation).getByRole("button", { name: /Coleta automática/ })).toBeTruthy();
    expect(within(navigation).queryByRole("button", { name: /Serviços Aplicações hospedadas/ })).toBeNull();
    expect(within(navigation).queryByRole("button", { name: /Bancos de dados/ })).toBeNull();
    expect(within(navigation).queryByRole("button", { name: /Redes/ })).toBeNull();
    expect(within(navigation).queryByRole("button", { name: /Integrações/ })).toBeNull();
    expect(within(navigation).queryByRole("button", { name: /Planos de ação/ })).toBeNull();
  });
});

describe("databases", () => {
  it("hides consumer services without services.view and never requests them", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: { ...INVENTORY_VIEWER, can_view_services: false } },
      [`/database-instances/${DATABASE_ID}`]: { data: database() },
      [`/database-instances/${DATABASE_ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/databases/${DATABASE_ID}`);
    expect(await screen.findByText("Hospedagem e operação")).toBeTruthy();
    expect(screen.queryByText("Serviços que utilizam este banco")).toBeNull();
    expect(requestedPaths(fetchMock).some((p) => p.endsWith("/consumers"))).toBe(false);
  });

  it("lists consumers and shows link history details", async () => {
    mockApi({
      "/me/capabilities": { data: INVENTORY_MANAGER },
      [`/database-instances/${DATABASE_ID}`]: { data: database() },
      [`/database-instances/${DATABASE_ID}/consumers`]: { data: [CONSUMER] },
      [`/database-instances/${DATABASE_ID}/history`]: {
        data: [
          {
            id: "e1",
            entity_type: "database_consumer",
            entity_id: CONSUMER.id,
            event_type: "database_consumer_removed",
            changes: {
              database_instance: { id: DATABASE_ID, code: "DB-0001", name: "ERP_PROD" },
              service: { id: SERVICE_ID, code: "SVC-0001", name: "Portal Interno" },
            },
            actor_name: "Ana Souza",
            occurred_at: "2026-11-06T10:00:00Z",
          },
        ],
      },
    });
    renderAt(`/apps/it-portal/databases/${DATABASE_ID}`);
    expect(await screen.findByText("Serviços que utilizam este banco")).toBeTruthy();
    expect(await screen.findByText("Leitura e escrita")).toBeTruthy();
    expect(await screen.findByText("Vínculo serviço–banco removido")).toBeTruthy();
    expect(screen.getByText("SVC-0001 · Portal Interno usa DB-0001 · ERP_PROD")).toBeTruthy();
  });
});


describe("Windows automatic inventory (E4.S3)", () => {
  it("shows Windows CPU, memory, volumes, uptime and services without Linux-only sections", async () => {
    mockApi({
      ...serverDetailRoutes(INVENTORY_VIEWER),
      [`/servers/${SERVER_ID}/observations/latest`]: {
        data: {
          id: "1c1f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f",
          server_id: SERVER_ID,
          run_id: "win-obs-0001",
          source: "windows_host_collector",
          collector_client_id: "it-portal-windows-pilot01",
          observed_at: "2026-11-11T16:49:09Z",
          received_at: "2026-11-11T16:49:10Z",
          schema_version: "1",
          status: "complete",
          summary: {
            os: { name: "Microsoft Windows Server 2019 Standard", version: "10.0.17763" },
            cpu_logical: 8,
            cpu_usage_percent: 33,
            uptime_seconds: 7824971,
            memory: { total_bytes: 47243603968, available_bytes: 5511974912 },
            volumes: [{ mount_point: "I:", size_bytes: 323175000000,
                        used_bytes: 314775000000, used_percent: 97.39 }],
            windows_services: [{ name: "EventLog", active_state: "running", sub_state: "automatic" }],
          },
          sections_status: { os: "ok", cpu: "ok", memory: "ok", volumes: "ok", windows_services: "ok" },
          divergences: [],
          created_at: "2026-11-11T16:49:10Z",
          presentation_status: "available",
        },
      },
    });
    renderAt(`/apps/it-portal/servers/${SERVER_ID}`);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /Coleta automática/ }));
    expect(await screen.findByText("Serviços Windows observados")).toBeTruthy();
    expect(screen.getByText("8 CPUs lógicas · amostra")).toBeTruthy();
    expect(screen.getByText("33%")).toBeTruthy();
    expect(screen.getByText("Tempo desde a última inicialização")).toBeTruthy();
    expect(screen.getByRole("progressbar", { name: "Utilização de Memória" })).toBeTruthy();
    expect(screen.getAllByText(/97,39%/).length).toBeGreaterThan(0);
    expect(screen.getByText("Uso elevado")).toBeTruthy();
    expect(screen.getByText(/EventLog/)).toBeTruthy();
    expect(screen.queryByText("Docker")).toBeNull();
    expect(screen.queryByText("Swap total")).toBeNull();
  });
});
