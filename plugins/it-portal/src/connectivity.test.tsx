import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  Capabilities,
  Integration,
  Network,
  Server,
  ServerNetworkLink,
  Service,
  ServiceDependency,
  ServiceHosting,
} from "./api/itPortalApi";
import { mockApi, renderAt, requestBodies, requestedPaths } from "./test/harness";

const SERVER_ID = "4b6f1c1e-2f8a-4c3b-9d7e-0a1b2c3d4e5f";
const SERVICE_ID = "7c1d2e3f-4a5b-4c6d-8e9f-0a1b2c3d4e5f";
const OTHER_SERVICE_ID = "8d2e3f4a-5b6c-4d7e-9f0a-1b2c3d4e5f6a";
const NETWORK_ID = "2b3c4d5e-6f7a-4b8c-9d0e-1f2a3b4c5d6e";
const LINK_ID = "3c4d5e6f-7a8b-4c9d-8e1f-2a3b4c5d6e7f";
const INTEGRATION_ID = "4d5e6f7a-8b9c-4d0e-9f2a-3b4c5d6e7f8a";
const DEPENDENCY_ID = "5e6f7a8b-9c0d-4e1f-8a3b-4c5d6e7f8a9b";

const NO_CONNECTIVITY: Capabilities = {
  display_name: "Ana Souza",
  can_view_servers: true,
  can_manage_servers: true,
  can_create_notes: true,
  can_view_action_plans: false,
  can_manage_action_plans: false,
  can_view_services: true,
  can_manage_services: true,
  can_view_databases: true,
  can_manage_databases: true,
  can_view_networks: false,
  can_manage_networks: false,
  can_view_integrations: false,
  can_manage_integrations: false,
};

const CONNECTIVITY_MANAGER: Capabilities = {
  ...NO_CONNECTIVITY,
  can_view_networks: true,
  can_manage_networks: true,
  can_view_integrations: true,
  can_manage_integrations: true,
};

const CONNECTIVITY_VIEWER: Capabilities = {
  ...CONNECTIVITY_MANAGER,
  can_manage_servers: false,
  can_create_notes: false,
  can_manage_services: false,
  can_manage_databases: false,
  can_manage_networks: false,
  can_manage_integrations: false,
};

const SERVER_SUMMARY = {
  id: SERVER_ID,
  code: "SRV-0001",
  name: "SRV-API",
  hostname: "srv-api.delpi.local",
  environment: "production" as const,
  unit_code: "01" as const,
  archived: false,
};

const SERVICE_SUMMARY = {
  id: SERVICE_ID,
  code: "SVC-0001",
  name: "Portal Interno",
  service_kind: "business_application" as const,
  environment: "production" as const,
  criticality: "high" as const,
  archived: false,
};

const OTHER_SERVICE_SUMMARY = {
  ...SERVICE_SUMMARY,
  id: OTHER_SERVICE_ID,
  code: "SVC-0002",
  name: "Keycloak",
  service_kind: "platform_service" as const,
  criticality: "critical" as const,
};

const NETWORK_SUMMARY = {
  id: NETWORK_ID,
  code: "NET-0001",
  name: "VLAN Servidores",
  cidr: "10.0.1.0/24",
  vlan_id: 10,
  network_scope: "corporate" as const,
  environment: "production" as const,
  unit_code: "01" as const,
  archived: false,
};

function server(overrides: Partial<Server> = {}): Server {
  return {
    ...SERVER_SUMMARY,
    ip_address: "10.0.1.20",
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
    ...SERVICE_SUMMARY,
    description: null,
    service_type: "web_application",
    technology: "Python/FastAPI",
    unit_code: "01",
    port: 8443,
    responsible: "Equipe Sistemas",
    administrative_status: "in_operation",
    revision: 1,
    archived_at: null,
    archived_by_name: null,
    hosting_count: 1,
    database_count: 0,
    created_at: "2026-11-03T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-03T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

function network(overrides: Partial<Network> = {}): Network {
  return {
    ...NETWORK_SUMMARY,
    gateway: "10.0.1.1",
    location: "Datacenter matriz",
    purpose: "Servidores de aplicação",
    zone: "servidores",
    criticality: "high",
    responsible: "Equipe Infra",
    notes: null,
    revision: 1,
    archived_at: null,
    archived_by_name: null,
    server_count: 1,
    created_at: "2026-11-04T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-04T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

function integration(overrides: Partial<Integration> = {}): Integration {
  return {
    id: INTEGRATION_ID,
    code: "INT-0001",
    name: "Envio de NF-e",
    source_service_id: SERVICE_ID,
    source_external_name: null,
    source_service: SERVICE_SUMMARY,
    target_service_id: null,
    target_external_name: "SEFAZ",
    target_service: null,
    protocol: "soap",
    direction: "source_to_target",
    purpose: "Autorização de notas",
    criticality: "critical",
    responsible: "Equipe Fiscal",
    administrative_status: "in_operation",
    notes: null,
    revision: 1,
    archived: false,
    archived_at: null,
    archived_by_name: null,
    created_at: "2026-11-05T12:00:00Z",
    created_by_name: "Ana Souza",
    updated_at: "2026-11-05T12:00:00Z",
    updated_by_name: "Ana Souza",
    ...overrides,
  };
}

const LINK: ServerNetworkLink = {
  id: LINK_ID,
  server_id: SERVER_ID,
  network_id: NETWORK_ID,
  ip_address: "10.0.1.20",
  interface_name: "ens192",
  notes: null,
  created_at: "2026-11-05T12:00:00Z",
  created_by_name: "Ana Souza",
  server: SERVER_SUMMARY,
  network: NETWORK_SUMMARY,
};

const HOSTING: ServiceHosting = {
  id: "9f8e7d6c-5b4a-4c3d-8e2f-1a0b9c8d7e6f",
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

const DEPENDENCY: ServiceDependency = {
  id: DEPENDENCY_ID,
  dependent_service_id: SERVICE_ID,
  required_service_id: OTHER_SERVICE_ID,
  notes: "Autenticação",
  created_at: "2026-11-05T12:00:00Z",
  created_by_name: "Ana Souza",
  dependent_service: SERVICE_SUMMARY,
  required_service: OTHER_SERVICE_SUMMARY,
};

const page = <T,>(items: T[]) => ({ data: { items, total: items.length, page: 1, page_size: 20 } });

function serverPageRoutes(caps: Capabilities) {
  return {
    "/me/capabilities": { data: caps },
    [`/servers/${SERVER_ID}`]: { data: server() },
    [`/servers/${SERVER_ID}/notes`]: { data: [] },
    [`/servers/${SERVER_ID}/history`]: { data: [] },
    [`/servers/${SERVER_ID}/observations/latest`]: { data: null },
    [`/servers/${SERVER_ID}/service-hostings`]: { data: [HOSTING] },
    "/database-instances": page([]),
    [`/servers/${SERVER_ID}/network-links`]: { data: [LINK] },
    [`/servers/${SERVER_ID}/integrations`]: { data: [integration()] },
    [`DELETE /server-network-links/${LINK_ID}`]: { data: { id: LINK_ID } },
  };
}

function servicePageRoutes(caps: Capabilities) {
  return {
    "/me/capabilities": { data: caps },
    [`/services/${SERVICE_ID}`]: { data: service() },
    [`/services/${SERVICE_ID}/hostings`]: { data: [HOSTING] },
    [`/services/${SERVICE_ID}/database-instances`]: { data: [] },
    [`/services/${SERVICE_ID}/history`]: { data: [] },
    [`/services/${SERVICE_ID}/integrations`]: { data: [integration()] },
    [`/services/${SERVICE_ID}/dependencies`]: { data: [DEPENDENCY] },
    "/services": page([service(), service({ ...OTHER_SERVICE_SUMMARY })]),
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

describe("connectivity navigation and access", () => {
  it("adds Redes and Integrações to the nav only with their view capabilities", async () => {
    mockApi({ "/me/capabilities": { data: CONNECTIVITY_VIEWER } });
    renderAt("/apps/it-portal/help");
    const nav = await screen.findByRole("navigation", { name: "Navegação do Portal de TI" });
    expect(within(nav).getAllByText("Redes").length).toBeGreaterThan(0);
    expect(within(nav).getAllByText("Integrações").length).toBeGreaterThan(0);
  });

  it("keeps the E2A nav for users without connectivity permissions", async () => {
    mockApi({ "/me/capabilities": { data: NO_CONNECTIVITY } });
    renderAt("/apps/it-portal/help");
    const nav = await screen.findByRole("navigation", { name: "Navegação do Portal de TI" });
    expect(within(nav).getAllByText("Serviços").length).toBeGreaterThan(0);
    expect(within(nav).queryByText("Redes")).toBeNull();
    expect(within(nav).queryByText("Integrações")).toBeNull();
  });

  it.each([
    ["/apps/it-portal/networks", "/networks"],
    [`/apps/it-portal/networks/${NETWORK_ID}`, "/networks"],
    ["/apps/it-portal/integrations", "/integrations"],
    [`/apps/it-portal/integrations/${INTEGRATION_ID}`, "/integrations"],
  ])("blocks %s without the view capability and never calls the API", async (path, apiPrefix) => {
    const fetchMock = mockApi({ "/me/capabilities": { data: NO_CONNECTIVITY } });
    renderAt(path);
    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
    expect(requestedPaths(fetchMock).some((p) => p.startsWith(apiPrefix))).toBe(false);
  });
});

describe("networks", () => {
  it("lists networks with CIDR and VLAN and hides management for viewers", async () => {
    mockApi({ "/me/capabilities": { data: CONNECTIVITY_VIEWER }, "/networks": page([network()]) });
    renderAt("/apps/it-portal/networks");
    expect(await screen.findByText("VLAN Servidores")).toBeTruthy();
    expect(screen.getByText("10.0.1.0/24 · VLAN 10")).toBeTruthy();
    expect(screen.getAllByText("Rede corporativa").length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /Cadastrar rede/ })).toBeNull();
  });

  it("shows the backend CIDR validation error when creating a network", async () => {
    mockApi({
      "/me/capabilities": { data: CONNECTIVITY_MANAGER },
      "/networks": page([]),
      "POST /networks": {
        status: 422,
        body: {
          success: false,
          message: "Revise os campos destacados da rede.",
          data: {
            error: {
              code: "invalid_network",
              details: { fields: { cidr: "Informe o endereço da rede com prefixo, por exemplo 10.0.1.0/24." } },
            },
          },
        },
      },
    });
    renderAt("/apps/it-portal/networks");
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar rede/ }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Cadastrar" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Revise os campos destacados da rede.")).toBeTruthy();
    expect(within(alert).getByText(/por exemplo 10.0.1.0\/24/)).toBeTruthy();
  });

  it("shows connected servers on the network page and unlinks without deleting either side", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CONNECTIVITY_MANAGER },
      [`/networks/${NETWORK_ID}`]: { data: network() },
      [`/networks/${NETWORK_ID}/server-links`]: { data: [LINK] },
      [`/networks/${NETWORK_ID}/history`]: { data: [] },
      [`DELETE /server-network-links/${LINK_ID}`]: { data: { id: LINK_ID } },
    });
    renderAt(`/apps/it-portal/networks/${NETWORK_ID}`);
    expect(await screen.findByText("Servidores conectados")).toBeTruthy();
    expect(await screen.findByText("SRV-API")).toBeTruthy();
    expect(screen.getByText("ens192")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Remover vínculo entre SRV-API e a rede VLAN Servidores" }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Nenhum cadastro é excluído/)).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Remover vínculo" }));
    await waitFor(() => expect(requestedPaths(fetchMock, "DELETE")).toEqual([`/server-network-links/${LINK_ID}`]));
  });

  it("makes archived networks read-only", async () => {
    mockApi({
      "/me/capabilities": { data: CONNECTIVITY_MANAGER },
      [`/networks/${NETWORK_ID}`]: { data: network({ archived: true, archived_at: "2026-11-06T10:00:00Z", archived_by_name: "Ana Souza" }) },
      [`/networks/${NETWORK_ID}/server-links`]: { data: [LINK] },
      [`/networks/${NETWORK_ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/networks/${NETWORK_ID}`);
    expect(await screen.findByRole("button", { name: /Restaurar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Editar/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Vincular servidor/ })).toBeNull();
  });
});

describe("server page — AC-08", () => {
  it("navigates services, databases, networks and integrations without a giant page", async () => {
    mockApi(serverPageRoutes(CONNECTIVITY_MANAGER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(screen.queryByText("Serviços hospedados")).toBeNull();

    fireEvent.click(within(navigation).getByText("Serviços"));
    expect(await screen.findByText("Serviços hospedados")).toBeTruthy();
    fireEvent.click(within(navigation).getByRole("button", { name: /Bancos de dados/ }));
    expect(await screen.findByText("Bancos de dados associados")).toBeTruthy();
    expect(screen.queryByText("Serviços hospedados")).toBeNull();

    fireEvent.click(within(navigation).getByRole("button", { name: /Redes/ }));
    expect(await screen.findByText("VLAN Servidores")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Vincular rede/ })).toBeTruthy();

    fireEvent.click(within(navigation).getByRole("button", { name: /Integrações/ }));
    expect(await screen.findByText("Integrações dos serviços hospedados")).toBeTruthy();
    expect(await screen.findByText("Envio de NF-e")).toBeTruthy();
    expect(screen.getByText("SEFAZ")).toBeTruthy();
    expect(screen.queryByText("VLAN Servidores")).toBeNull();
  });

  it("hides connectivity management from viewers in the selected area", async () => {
    mockApi(serverPageRoutes(CONNECTIVITY_VIEWER));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /Redes/ }));
    expect(await screen.findByText("VLAN Servidores")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Vincular rede/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Remover vínculo/ })).toBeNull();
  });

  it("does not render or fetch restricted connectivity areas", async () => {
    const fetchMock = mockApi(serverPageRoutes(NO_CONNECTIVITY));
    renderAt("/apps/it-portal/servers/" + SERVER_ID);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    expect(within(navigation).queryByRole("button", { name: /^Redes/ })).toBeNull();
    expect(within(navigation).queryByRole("button", { name: /^Integrações/ })).toBeNull();
    fireEvent.click(within(navigation).getByRole("button", { name: /^Serviços/ }));
    expect(await screen.findByText("Serviços hospedados")).toBeTruthy();
    expect(screen.queryByText("Integrações dos serviços hospedados")).toBeNull();
    const paths = requestedPaths(fetchMock);
    expect(paths.some((p) => p.endsWith("/network-links") || p.endsWith("/integrations"))).toBe(false);
  });
});

describe("service page — integrations and dependencies", () => {
  it("lists integrations and operational dependencies with explicit relation", async () => {
    mockApi(servicePageRoutes(CONNECTIVITY_MANAGER));
    renderAt(`/apps/it-portal/services/${SERVICE_ID}`);
    expect(await screen.findByText("Envio de NF-e")).toBeTruthy();
    expect(await screen.findByText("Dependências operacionais")).toBeTruthy();
    expect(await screen.findByText("Depende de")).toBeTruthy();
    expect(screen.getByText("Keycloak")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Registrar dependência/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Cadastrar integração/ })).toBeTruthy();
  });

  it("creates an integration from the service page with the service as source", async () => {
    const fetchMock = mockApi({
      ...servicePageRoutes(CONNECTIVITY_MANAGER),
      "POST /integrations": { status: 201, data: integration() },
    });
    renderAt(`/apps/it-portal/services/${SERVICE_ID}`);
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar integração/ }));
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText(/Não registre credenciais, tokens nem payloads/)).toBeTruthy();
    fireEvent.click(within(dialog).getByRole("button", { name: "Cadastrar" }));
    await waitFor(() => expect(requestBodies(fetchMock, "POST")).toHaveLength(1));
    expect(requestBodies(fetchMock, "POST")[0]).toMatchObject({
      source_service_id: SERVICE_ID,
      source_external_name: null,
      target_service_id: null,
      target_external_name: null,
    });
  });

  it("hides dependency and integration management for viewers", async () => {
    mockApi(servicePageRoutes(CONNECTIVITY_VIEWER));
    renderAt(`/apps/it-portal/services/${SERVICE_ID}`);
    expect(await screen.findByText("Depende de")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Registrar dependência/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Cadastrar integração/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Remover dependência/ })).toBeNull();
  });

  it("does not request integrations without integrations.view", async () => {
    const fetchMock = mockApi(servicePageRoutes(NO_CONNECTIVITY));
    renderAt(`/apps/it-portal/services/${SERVICE_ID}`);
    expect(await screen.findByText("Dependências operacionais")).toBeTruthy();
    expect(requestedPaths(fetchMock).some((p) => p.endsWith("/integrations"))).toBe(false);
  });
});

describe("integrations", () => {
  it("renders internal and external endpoints and the history of link changes", async () => {
    mockApi({
      "/me/capabilities": { data: CONNECTIVITY_VIEWER },
      [`/integrations/${INTEGRATION_ID}`]: { data: integration() },
      [`/integrations/${INTEGRATION_ID}/history`]: {
        data: [
          {
            id: "e1",
            entity_type: "integration",
            entity_id: INTEGRATION_ID,
            event_type: "integration_updated",
            changes: { protocol: { from: "http_api", to: "soap" } },
            actor_name: "Ana Souza",
            occurred_at: "2026-11-06T10:00:00Z",
          },
        ],
      },
    });
    renderAt(`/apps/it-portal/integrations/${INTEGRATION_ID}`);
    expect(await screen.findByText("Portal Interno")).toBeTruthy();
    expect(screen.getByText("SEFAZ")).toBeTruthy();
    expect(screen.getByText("Sistema externo")).toBeTruthy();
    expect(await screen.findByText("Integração atualizada")).toBeTruthy();
    expect(screen.getByText("Campos alterados: Protocolo")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Editar/ })).toBeNull();
  });

  it("describes server–network and dependency history events", async () => {
    mockApi({
      ...serverPageRoutes(CONNECTIVITY_VIEWER),
      [`/servers/${SERVER_ID}/history`]: {
        data: [
          {
            id: "e2",
            entity_type: "server_network_link",
            entity_id: LINK_ID,
            event_type: "server_network_link_removed",
            changes: {
              server: { id: SERVER_ID, code: "SRV-0001", name: "SRV-API" },
              network: { id: NETWORK_ID, code: "NET-0001", name: "VLAN Servidores", cidr: "10.0.1.0/24" },
              ip_address: "10.0.1.20",
            },
            actor_name: "Ana Souza",
            occurred_at: "2026-11-06T10:00:00Z",
          },
        ],
      },
    });
    renderAt(`/apps/it-portal/servers/${SERVER_ID}`);
    const navigation = await screen.findByRole("navigation", { name: "Seções deste servidor" });
    fireEvent.click(within(navigation).getByRole("button", { name: /^Histórico/ }));
    expect(await screen.findByText("Vínculo servidor–rede removido")).toBeTruthy();
    expect(screen.getByText("SRV-0001 · SRV-API na rede NET-0001 · VLAN Servidores com IP 10.0.1.20")).toBeTruthy();
  });
});

describe("help", () => {
  it("documents networks, integrations, relation types and the new permissions", async () => {
    mockApi({ "/me/capabilities": { data: NO_CONNECTIVITY } });
    renderAt("/apps/it-portal/help");
    expect(await screen.findByRole("heading", { name: "Cadastrar redes e conectar servidores" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Registrar integrações entre sistemas" })).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Diferença entre hospedagem, conectividade, consumo e dependência" }),
    ).toBeTruthy();
    expect(screen.getAllByText("Gerenciar integrações").length).toBeGreaterThan(0);
  });
});
