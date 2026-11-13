import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Capabilities, Workstation } from "../../api/itPortalApi";
import { mockApi, renderAt } from "../../test/harness";

const ID = "0dba8c08-61f5-45c7-af1e-e648f76c6a99";
const CAPS: Capabilities = {
  display_name: "TI", can_view_servers: false, can_manage_servers: false,
  can_view_computers: true, can_manage_computers: false,
  can_manage_host_services: false, can_control_host_services: false,
  can_create_notes: false, can_view_action_plans: false, can_manage_action_plans: false,
  can_view_services: false, can_manage_services: false,
  can_view_databases: false, can_manage_databases: false,
  can_view_networks: false, can_manage_networks: false,
  can_view_integrations: false, can_manage_integrations: false,
};
const computer: Workstation = {
  id: ID, code: "PC-0001", name: "PC TI", hostname: "pc-teste-001",
  ip_address: null, unit_code: "02", device_kind: "desktop",
  department: "TI", location: null, responsible: null,
  responsible_user_id: null, operating_system: "Windows 11",
  administrative_status: "in_operation", description: null,
  revision: 1, archived: false, archived_at: null, archived_by_name: null,
  created_at: "2026-11-13T12:00:00Z", created_by_name: "TI",
  updated_at: "2026-11-13T12:00:00Z", updated_by_name: "TI",
};

afterEach(() => cleanup());

describe("G2-S2: inventario observado", () => {
  it("renders a distinct observed snapshot and never suggests a live connection", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: computer },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: {
        data: {
          observed_at: "2026-11-13T15:00:00Z",
          received_at: "2026-11-13T15:01:00Z",
          status: "partial",
          freshness: "stale",
          snapshot: {
            source: "windows_workstation_local_v1", schema_version: "1",
            run_id: "2bb2c32d-d851-4e93-8f8a-cd845671c32a",
            observed_at: "2026-11-13T15:00:00Z", status: "partial",
            host: { hostname: "pc-teste-001" },
            hardware: {
              manufacturer: "Fabricante Teste", model: "Modelo Teste",
              cpu_name: "Processador Teste", logical_processors: 8,
              memory_total_bytes: 17179869184,
            },
            os: {
              name: "Microsoft Windows 11 Pro", version: "10.0.26200",
              build_number: "26200", architecture: "64-bit", uptime_seconds: 3600,
            },
            volumes: [{
              mount_point: "C:", filesystem: "NTFS",
              capacity_bytes: 1000000000000, free_bytes: 500000000000,
            }],
            network: { private_ipv4: [] },
            sections_status: {
              hardware: "ok", os: "ok", volumes: "ok", network: "unavailable",
            },
          },
        },
      },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText("Processador Teste")).toBeTruthy();
    expect(screen.getByText("16.0 GB")).toBeTruthy();
    expect(screen.getByText("Desatualizado")).toBeTruthy();
    expect(screen.getByText(/Não indica presença online/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Conectar|Acesso remoto/ })).toBeNull();
  });

  it("explains that the pilot has no telemetry before the first S2S collection", async () => {
    mockApi({
      "/me/capabilities": { data: CAPS },
      [`/workstations/${ID}`]: { data: computer },
      [`/workstations/${ID}/history`]: { data: [] },
      [`/workstations/${ID}/snapshot`]: { data: null },
    });
    renderAt(`/apps/it-portal/workstations/${ID}`);
    expect(await screen.findByText(/Nenhuma coleta automática registrada/)).toBeTruthy();
  });
});
