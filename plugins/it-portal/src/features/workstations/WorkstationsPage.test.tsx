import { cleanup, fireEvent, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Capabilities, Workstation } from "../../api/itPortalApi";
import { mockApi, renderAt, requestedPaths } from "../../test/harness";

const ID = "0dba8c08-61f5-45c7-af1e-e648f76c6a99";

const CAPS: Capabilities = {
  display_name: "TI Delpi",
  can_view_servers: false,
  can_manage_servers: false,
  can_view_computers: true,
  can_manage_computers: true,
  can_manage_host_services: false,
  can_control_host_services: false,
  can_create_notes: false,
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

function computer(overrides: Partial<Workstation> = {}): Workstation {
  return {
    id: ID,
    code: "PC-0001",
    name: "PC Engenharia",
    hostname: "pc-eng-001.delpi.local",
    ip_address: "192.0.2.12",
    unit_code: "01",
    device_kind: "desktop",
    department: "Engenharia",
    location: "Matriz",
    responsible: "TI",
    operating_system: "Windows 11",
    administrative_status: "in_operation",
    description: "Computador corporativo",
    revision: 1,
    archived: false,
    archived_at: null,
    archived_by_name: null,
    created_at: "2026-11-13T12:00:00Z",
    created_by_name: "TI Delpi",
    updated_at: "2026-11-13T12:00:00Z",
    updated_by_name: "TI Delpi",
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("G1-UI: computadores", () => {
  it("blocks inventory requests without computers.view even if servers.view exists", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": {
        data: { ...CAPS, can_view_computers: false, can_manage_computers: false, can_view_servers: true },
      },
    });
    renderAt("/apps/it-portal/workstations");
    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
    expect(requestedPaths(fetchMock).some((path) => path.startsWith("/workstations"))).toBe(false);
  });

  it("lists computers from BFF and hides management for read-only operators", async () => {
    mockApi({
      "/me/capabilities": { data: { ...CAPS, can_manage_computers: false } },
      "/workstations": { data: { items: [computer()], total: 1, page: 1, page_size: 20 } },
    });
    renderAt("/apps/it-portal/workstations");
    expect(await screen.findByText("pc-eng-001.delpi.local")).toBeTruthy();
    expect(screen.getByText("Engenharia")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Cadastrar computador/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Conectar/ })).toBeNull();
  });

  it("shows backend field errors in the creation modal", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/workstations": { data: { items: [], total: 0, page: 1, page_size: 20 } },
      "POST /workstations": {
        status: 422,
        body: {
          success: false,
          message: "Dados inválidos.",
          data: { error: { code: "invalid_workstation", details: { fields: { hostname: "Hostname inválido." } } } },
        },
      },
    });
    renderAt("/apps/it-portal/workstations");
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar computador/ }));
    expect(await screen.findByText(/Nenhum agente ou acesso remoto será ativado/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("Hostname inválido.")).toBeTruthy();
    expect(requestedPaths(fetchMock, "POST")).toContain("/workstations");
  });

  it("keeps archived computers read-only and shows audit history", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: {
        data: computer({ archived: true, archived_at: "2026-11-13T13:00:00Z", archived_by_name: "TI Delpi" }),
      },
      [`/workstations/${ID}/history`]: {
        data: [{
          id: "a5e2daff-532d-4e98-a8c1-fcf3a4db037d",
          entity_type: "workstation",
          entity_id: ID,
          event_type: "workstation_archived",
          changes: {},
          actor_name: "TI Delpi",
          occurred_at: "2026-11-13T13:00:00Z",
        }],
      },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByRole("button", { name: /Restaurar/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Editar$/ })).toBeNull();
    expect(screen.queryByRole("button", { name: /Conectar/ })).toBeNull();
    expect(screen.getByText(/Agente de inventário e acesso remoto ainda não implantados/)).toBeTruthy();
    expect(screen.getByText(/Computador arquivado em/)).toBeTruthy();
  });

  it("offers editing to authorized operators but never remote access", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: computer() },
      [`/workstations/${ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    fireEvent.click(await screen.findByRole("button", { name: /^Editar$/ }));
    expect(await screen.findByText(/Hostname único entre cadastros ativos/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Conectar|Acesso remoto/ })).toBeNull();
  });
});
