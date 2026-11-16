import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Capabilities, AtlasJournalEntry } from "../../api/itPortalApi";
import { mockApi, renderAt, requestedPaths } from "../../test/harness";

const PROPOSAL = "01234567-89ab-4def-8abc-0123456789ab";
const CAPS: Capabilities = {
  display_name: "Operadora de TI",
  can_view_servers: false, can_manage_servers: false,
  can_view_computers: false, can_manage_computers: false,
  can_manage_host_services: false, can_control_host_services: false,
  can_create_notes: false, can_view_action_plans: false, can_manage_action_plans: false,
  can_view_services: false, can_manage_services: false,
  can_view_databases: false, can_manage_databases: false,
  can_view_networks: false, can_manage_networks: false,
  can_view_integrations: false, can_manage_integrations: false,
  can_view_atlas_deployments: true,
};

const ENTRY: AtlasJournalEntry = {
  id: PROPOSAL,
  requester_subject: "11111111-2222-4333-8444-555555555555",
  request_id: "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
  environment: "prod",
  service_id: "public-hub",
  status: "pending_approval",
  target_commit_sha: "f81ddd0075de1e4ef8bb68ca58791e9c43e70759",
  base_commit_sha: "03cecb7ed90946c799a66ca9b22b45beb221282e",
  manifest_digest: "sha256:" + "a".repeat(64),
  previous_image_id: "sha256:" + "b".repeat(64),
  target_image_id: "sha256:" + "c".repeat(64),
  rollback_image_id: "sha256:" + "b".repeat(64),
  binding_sha256: "d".repeat(64),
  created_at: "2026-11-16T11:00:00Z",
  expires_at: "2026-11-16T11:10:00Z",
  expired: false,
  approved_by: null, approved_at: null, revision: 1,
  can_approve: false, can_execute: false,
};

const ROUTE = "/apps/it-portal/atlas-deployments";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ATLAS read-only journal behind Core capability", () => {
  it("renders real BFF rows and details without calling write endpoints", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/atlas/deployments": { data: { items: [ENTRY], total: 1, page: 1, page_size: 10 } },
      ["/atlas/deployments/" + PROPOSAL]: { data: {
        ...ENTRY, events: [{
          sequence: 1, event_type: "prepared", actor_subject: ENTRY.requester_subject,
          occurred_at: ENTRY.created_at,
        }],
      } },
    });
    renderAt(ROUTE);
    expect(await screen.findByRole("heading", { name: "Implantações ATLAS" })).toBeTruthy();
    expect(await screen.findByText(ENTRY.target_commit_sha.slice(0, 12))).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes da proposta " + PROPOSAL }));
    expect(await screen.findByText(ENTRY.manifest_digest)).toBeTruthy();
    expect(await screen.findByText(ENTRY.binding_sha256)).toBeTruthy();
    expect(screen.getByText(/consulta não representa aprovação/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Aprovar atualização" })).toBeNull();
    expect(requestedPaths(fetchMock, "POST")).toEqual([]);
    expect(requestedPaths(fetchMock, "PUT")).toEqual([]);
    expect(requestedPaths(fetchMock, "DELETE")).toEqual([]);
  });

  it("does not request journal when the backend capability is missing", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: { ...CAPS, can_view_atlas_deployments: false } },
    });
    renderAt(ROUTE);
    await waitFor(() => expect(requestedPaths(fetchMock)).toContain("/me/capabilities"));
    await waitFor(() => expect(screen.queryByText("Abrindo o Portal de TI")).toBeNull());
    expect(requestedPaths(fetchMock)).not.toContain("/atlas/deployments");
  });

  it("shows a safe empty state, not synthetic proposal data", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/atlas/deployments": { data: { items: [], total: 0, page: 1, page_size: 10 } },
    });
    renderAt(ROUTE);
    expect(await screen.findByText("Nenhuma solicitação encontrada.")).toBeTruthy();
    expect(screen.queryByText(ENTRY.manifest_digest)).toBeNull();
    expect(requestedPaths(fetchMock, "POST")).toEqual([]);
  });

  it("does not mask a disabled backend as an empty journal", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/atlas/deployments": { status: 503, body: {
        success: false, message: "Consulta de implantações ainda não habilitada.",
        data: { error: { code: "atlas_journal_disabled" } },
      } },
    });
    renderAt(ROUTE);
    expect(await screen.findByText(/consulta de implantações ainda não habilitada/i)).toBeTruthy();
    expect(screen.queryByText("Nenhuma solicitação encontrada.")).toBeNull();
    expect(requestedPaths(fetchMock, "POST")).toEqual([]);
  });

  it("filters by environment using GET query parameters only", async () => {
    const fetchMock = mockApi({
      "/me/capabilities": { data: CAPS },
      "/atlas/deployments": { data: { items: [ENTRY], total: 1, page: 1, page_size: 10 } },
    });
    renderAt(ROUTE);
    await screen.findByRole("heading", { name: "Implantações ATLAS" });
    fireEvent.change(screen.getByLabelText("Ambiente"), { target: { value: "hml" } });
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) =>
      String(url).includes("environment=hml"),
    )).toBe(true));
    expect(requestedPaths(fetchMock, "POST")).toEqual([]);
  });
});
