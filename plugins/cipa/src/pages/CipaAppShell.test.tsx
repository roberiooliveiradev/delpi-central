// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import type { CipaAccess } from "../security/cipaAccess";
import { CipaAppShell } from "./CipaAppShell";

const api = vi.hoisted(() => ({
  listMinutes: vi.fn(),
  listCipaMembers: vi.fn(),
  getMySignatureProfile: vi.fn(),
  getMinute: vi.fn(),
  getAudit: vi.fn(),
  exportPdf: vi.fn(),
}));

const navigation = vi.hoisted(() => ({
  navigateCipa: vi.fn(),
}));

vi.mock("../api/cipaApi", () => ({
  createCipaMember: vi.fn(),
  createMinute: vi.fn(),
  deleteCipaMember: vi.fn(),
  endCipaMember: vi.fn(),
  fetchMySignatureImageBlob: vi.fn(),
  exportPdf: api.exportPdf,
  finalizeMinute: vi.fn(),
  getAudit: api.getAudit,
  getMinute: api.getMinute,
  getSignatureImage: vi.fn(),
  getMySignatureProfile: api.getMySignatureProfile,
  getSignContext: vi.fn(),
  listCipaMembers: api.listCipaMembers,
  listMinutes: api.listMinutes,
  pendingSignatures: vi.fn(),
  refuseMinute: vi.fn(),
  searchDirectoryUsers: vi.fn(),
  sendForSignature: vi.fn(),
  setSigners: vi.fn(),
  signMinute: vi.fn(),
  updateCipaMember: vi.fn(),
  updateMinute: vi.fn(),
  updateMySignatureProfile: vi.fn(),
  uploadMySignatureImage: vi.fn(),
}));

vi.mock("../hooks/useCipaRouterPath", () => ({
  navigateCipa: navigation.navigateCipa,
}));

const access: CipaAccess = {
  admin: false,
  can_view: true,
  can_manage: true,
  can_sign: true,
  units: [
    {
      id: "01",
      label: "Santa Catarina",
      view: true,
      manage: true,
      sign: true,
    },
  ],
};

beforeAll(() => {
  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    configurable: true,
    value: vi.fn(() => ({
      beginPath: vi.fn(),
      fillRect: vi.fn(),
      lineTo: vi.fn(),
      moveTo: vi.fn(),
      stroke: vi.fn(),
    })),
  });
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:ata"),
  });
  Object.defineProperty(URL, "revokeObjectURL", {
    configurable: true,
    value: vi.fn(),
  });
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  api.listMinutes.mockResolvedValue({
    items: [
      {
        id: "minute-1",
        unit_code: "01",
        title: "Reunião ordinária",
        minute_number: "ATA-001",
        meeting_type: "ordinary",
        meeting_date: "2026-07-16",
        status: "draft",
        signatures_done: 0,
        signatures_pending: 2,
      },
    ],
    total: 1,
  });
  api.getMySignatureProfile.mockResolvedValue({
    display_name: "Ana",
    has_signature: false,
  });
  api.listCipaMembers.mockResolvedValue([
    {
      id: "member-1",
      unit_code: "01",
      user_id: "11111111-1111-1111-1111-111111111111",
      display_name: "Ana Presidente",
      role: "president",
      mandate_start: "2026-01-01",
      mandate_end: null,
      is_active: true,
    },
  ]);
  api.getAudit.mockResolvedValue({ items: [] });
  api.exportPdf.mockResolvedValue(new Blob(["pdf"], { type: "application/pdf" }));
  api.getMinute.mockResolvedValue({
    minute: {
      id: "minute-1",
      unit_code: "01",
      title: "Reunião ordinária",
      minute_number: "2026/001",
      meeting_type: "ordinary",
      meeting_date: "2026-07-16",
      status: "draft",
    },
    version: { body_html: "<p>Documento da ata.</p>", content_hash: "hash" },
    participants: [],
    signers: [],
    signatures: [],
    action_items: [],
    versions: [],
  });
});

describe("CipaAppShell compartilhado", () => {
  it("renderiza header, filtros e DataTable navegável na lista", async () => {
    const { container } = render(
      <CipaAppShell
        route={{ kind: "list", unitCode: "01" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "CIPA — Santa Catarina" }),
    ).toBeTruthy();
    expect(screen.getByLabelText("Status")).toBeTruthy();
    expect(screen.getByLabelText("Busca")).toBeTruthy();

    await screen.findByText("Reunião ordinária");
    const table = container.querySelector(".delpi-ui-table");
    const row = container.querySelector(".delpi-ui-table__row--clickable");
    expect(table).toBeTruthy();
    expect(row).toBeTruthy();

    fireEvent.keyDown(row!, { key: "Enter" });
    expect(navigation.navigateCipa).toHaveBeenCalledWith(
      "/apps/cipa/filial-01/minutes/minute-1",
    );
  });

  it("renderiza estado de acesso negado pelo componente canônico", () => {
    const { container } = render(
      <CipaAppShell
        route={{ kind: "pending" }}
        access={{ ...access, can_sign: false }}
        accessLoading={false}
        accessError={null}
      />,
    );

    expect(screen.getByRole("heading", { name: "Sem acesso" })).toBeTruthy();
    expect(container.querySelector(".delpi-ui-state-box--error")).toBeTruthy();
  });

  it("navega para membros e cargos a partir da listagem", async () => {
    render(
      <CipaAppShell
        route={{ kind: "list", unitCode: "01" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Membros e cargos/ }));
    expect(navigation.navigateCipa).toHaveBeenCalledWith("/apps/cipa/filial-01/members");
  });

  it("renderiza a gestão de membros com composição ativa", async () => {
    render(
      <CipaAppShell
        route={{ kind: "members", unitCode: "01" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByRole("heading", { name: /Membros e cargos/ });
    expect(await screen.findByText("Ana Presidente")).toBeTruthy();
    expect(api.listCipaMembers).toHaveBeenCalled();
  });

  it("carrega o fluxo básico da assinatura pessoal", async () => {
    render(
      <CipaAppShell
        route={{ kind: "mySignature" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "Minha assinatura" })).toBeTruthy();
    });
    expect(screen.getByDisplayValue("Ana")).toBeTruthy();
    expect(screen.getByText("Nenhuma assinatura cadastrada ainda.")).toBeTruthy();
  });

  it("renderiza modo de leitura e baixa o PDF oficial", async () => {
    render(
      <CipaAppShell
        route={{ kind: "detail", unitCode: "01", minuteId: "minute-1" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByLabelText("Modo de leitura da ata");
    expect(screen.getByText("Documento da ata.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Baixar PDF/ }));
    await waitFor(() => expect(api.exportPdf).toHaveBeenCalledWith("minute-1"));
  });
});
