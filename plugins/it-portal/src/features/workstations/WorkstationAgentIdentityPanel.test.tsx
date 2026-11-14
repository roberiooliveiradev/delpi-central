import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Capabilities, Workstation } from "../../api/itPortalApi";
import { mockApi, renderAt, requestedPaths } from "../../test/harness";

const ID = "0dba8c08-61f5-45c7-af1e-e648f76c6a99";
const CAPS: Capabilities = {
  display_name: "TI", can_view_servers: false, can_manage_servers: false,
  can_view_computers: true, can_manage_computers: true,
  can_manage_host_services: false, can_control_host_services: false,
  can_create_notes: false, can_view_action_plans: false, can_manage_action_plans: false,
  can_view_services: false, can_manage_services: false,
  can_view_databases: false, can_manage_databases: false,
  can_view_networks: false, can_manage_networks: false,
  can_view_integrations: false, can_manage_integrations: false,
};

const workstation: Workstation = {
  id: ID, code: "PC-0001", name: "PC TI", hostname: "pc-teste-001",
  ip_address: null, unit_code: "02", device_kind: "desktop",
  department: "TI", location: null, responsible: null,
  responsible_user_id: null, operating_system: "Windows 11",
  administrative_status: "in_operation", description: null,
  revision: 1, archived: false, archived_at: null, archived_by_name: null,
  created_at: "2026-11-13T12:00:00Z", created_by_name: "TI",
  updated_at: "2026-11-13T12:00:00Z", updated_by_name: "TI",
};

function identity(canPrepare: boolean) {
  return {
    workstation_id: ID, client_id: null, state: "not_prepared",
    prepared_at: null, revocation_status: "none", can_prepare: canPrepare,
    can_revoke: false, credentials_issued: false,
    collector_enabled: false, remote_access_enabled: false,
  };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("G2-S4: identidade exclusiva no Keycloak", () => {
  it("shows disabled by default, without a provisioning button", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: workstation },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: { data: null },
      [`/workstations/${ID}/agent-identity`]: { data: identity(false) },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText("Ainda não preparada")).toBeTruthy();
    expect(screen.getByText("Desabilitada")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Preparar identidade/ })).toBeNull();
    expect(requestedPaths(fetchMock).some((path) => path.endsWith("/agent-identity/prepare"))).toBe(false);
  });

  it("prepares only after operator confirmation, with no credentials in the UI", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: workstation },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: { data: null },
      [`/workstations/${ID}/agent-identity`]: { data: identity(true) },
      [`POST /workstations/${ID}/agent-identity/prepare`]: {
        data: {
          workstation_id: ID, client_id: "itp-ws-" + ID.replace(/-/g, ""),
          state: "prepared", prepared_at: null, revocation_status: "none",
          can_prepare: false, can_revoke: false,
          credentials_issued: false, collector_enabled: false,
          remote_access_enabled: false,
        },
      },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    fireEvent.click(await screen.findByRole("button", { name: /Preparar identidade/ }));
    expect(screen.getByText(/Criar um Client individual e DESABILITADO/)).toBeTruthy();
    expect(requestedPaths(fetchMock).some((path) => path.endsWith("/agent-identity/prepare"))).toBe(false);
    const confirmationButtons = screen.getAllByRole("button", { name: /Preparar identidade/ });
    fireEvent.click(confirmationButtons[confirmationButtons.length - 1]);
    expect(await screen.findByText(/Identidade criada desabilitada no Keycloak/)).toBeTruthy();
    expect(requestedPaths(fetchMock, "POST").some((path) => path.endsWith("/agent-identity/prepare"))).toBe(true);
  });


  it("revokes only after explicit confirmation and keeps credentials invisible", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: workstation },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: { data: null },
      [`/workstations/${ID}/agent-identity`]: {
        data: {
          ...identity(false), client_id: "itp-ws-" + ID.replace(/-/g, ""),
          state: "prepared", can_revoke: true,
        },
      },
      [`POST /workstations/${ID}/agent-identity/revoke`]: {
        data: {
          ...identity(false), state: "revoked", revocation_status: "confirmed",
        },
      },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    fireEvent.click(await screen.findByRole("button", { name: /Revogar identidade/ }));
    expect(screen.getByText(/Revogar o vinculo do inventario/)).toBeTruthy();
    expect(requestedPaths(fetchMock, "POST").some(p => p.endsWith("/agent-identity/revoke"))).toBe(false);
    const actions = screen.getAllByRole("button", { name: /Revogar identidade/ });
    fireEvent.click(actions[actions.length - 1]);
    expect(await screen.findByText(/Identidade revogada/)).toBeTruthy();
    expect(requestedPaths(fetchMock, "POST").some(p => p.endsWith("/agent-identity/revoke"))).toBe(true);
  });

  it("never exposes the provisioning action to a read-only operator", async () => {
    mockApi({
      "/me/capabilities": { data: { ...CAPS, can_manage_computers: false } },
      [`/workstations/${ID}`]: { data: workstation },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: { data: null },
      [`/workstations/${ID}/agent-identity`]: { data: identity(true) },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText("Ainda não preparada")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Preparar identidade/ })).toBeNull();
  });
});
