import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Capabilities, Workstation } from "../../api/itPortalApi";
import { mockApi, renderAt, requestBodies, requestedPaths } from "../../test/harness";

const OWNER_ID = "5bd659b9-3816-48e3-9d9e-a2f53e96b8b7";
const ID = "0dba8c08-61f5-45c7-af1e-e648f76c6a99";
const CAPS: Capabilities = {
  display_name: "TI Delpi", can_view_servers: false, can_manage_servers: false,
  can_view_computers: true, can_manage_computers: true,
  can_manage_host_services: false, can_control_host_services: false,
  can_create_notes: false, can_view_action_plans: false, can_manage_action_plans: false,
  can_view_services: false, can_manage_services: false,
  can_view_databases: false, can_manage_databases: false,
  can_view_networks: false, can_manage_networks: false,
  can_view_integrations: false, can_manage_integrations: false,
};

function computer(overrides: Partial<Workstation> = {}): Workstation {
  return {
    id: ID, code: "PC-0001", name: "DLP-ES-TI-D01", hostname: "pc-test-001",
    ip_address: "192.0.2.30", unit_code: "02", device_kind: "desktop",
    department: "TI", location: "Filial ES", responsible: "Nome anterior",
    responsible_user_id: null, operating_system: "Windows 11", administrative_status: "in_operation",
    description: null, revision: 1, archived: false, archived_at: null, archived_by_name: null,
    created_at: "2026-11-13T12:00:00Z", created_by_name: "TI Delpi",
    updated_at: "2026-11-13T12:00:00Z", updated_by_name: "TI Delpi",
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("G1-OWNER: responsavel como usuario Core", () => {
  it("searches the official directory, selects owner by UUID and posts owner ID", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/workstations": { data: { items: [], page: 1, page_size: 25, total: 0 } },
      "/core-api/me/directory/users": {
        body: { items: [{ id: OWNER_ID, name: "Ana Colaboradora", email: "a***@delpi.com.br" }] },
      },
      "POST /workstations": {
        data: computer({ responsible: "Ana Colaboradora", responsible_user_id: OWNER_ID }),
      },
    });
    renderAt("/apps/it-portal/workstations");
    fireEvent.click(await screen.findByRole("button", { name: /Cadastrar computador/ }));
    fireEvent.change(screen.getByRole("searchbox", { name: /Responsável/ }), {
      target: { value: "Ana" },
    });
    fireEvent.click(await screen.findByRole("option", { name: /Ana Colaboradora/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar" }));

    await waitFor(() => expect(requestBodies(fetchMock, "POST").length).toBeGreaterThan(0));
    const body = requestBodies(fetchMock, "POST")[0] as Record<string, unknown>;
    expect(body.responsible_user_id).toBe(OWNER_ID);
    expect(body.responsible).toBe("Ana Colaboradora");
    expect(requestedPaths(fetchMock).includes("/core-api/me/directory/users")).toBe(true);
  });

  it("shows prior text owners without automatically linking matching names", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: computer() },
      [`/workstations/${ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    fireEvent.click(await screen.findByRole("button", { name: /^Editar$/ }));
    expect(await screen.findByText(/Cadastro anterior \(texto\): Nome anterior/)).toBeTruthy();
    expect(screen.getByRole("searchbox", { name: /Responsável/ })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Conectar/ })).toBeNull();
  });

  it("signals inactive owner while keeping the historical name readable", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: computer({ responsible_user_id: OWNER_ID, responsible: "Ana Colaboradora" }) },
      [`/workstations/${ID}/history`]: { data: [] },
      "POST /core-api/me/directory/users/lookup": { body: { items: [] } },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText(/Ana Colaboradora \(conta inativa ou indisponível\)/)).toBeTruthy();
  });

  it("does not open owner search without computer edit rights", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: { ...CAPS, can_manage_computers: false } },
      [`/workstations/${ID}`]: { data: computer() },
      [`/workstations/${ID}/history`]: { data: [] },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText(/Nome anterior \(cadastro anterior, sem vínculo\)/)).toBeTruthy();
    expect(screen.queryByRole("searchbox", { name: /Responsável/ })).toBeNull();
    expect(requestedPaths(fetchMock).includes("/core-api/me/directory/users")).toBe(false);
  });
});
