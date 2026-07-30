// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import type { ComiteEticaAccess } from "../security/cecAccess";
import { CecAppShell } from "./CecAppShell";

const api = vi.hoisted(() => ({
  createVersion: vi.fn(),
  deleteMinute: vi.fn(),
  listMinutes: vi.fn(),
  listComiteEticaMembers: vi.fn(),
  getMySignatureProfile: vi.fn(),
  getMinute: vi.fn(),
  getAudit: vi.fn(),
  exportPdf: vi.fn(),
  exportFilteredPdfs: vi.fn(),
}));

const navigation = vi.hoisted(() => ({
  navigateCec: vi.fn(),
}));

vi.mock("../api/cecApi", () => ({
  createComiteEticaMember: vi.fn(),
  createMinute: vi.fn(),
  createVersion: api.createVersion,
  deleteComiteEticaMember: vi.fn(),
  deleteMinute: api.deleteMinute,
  endComiteEticaMember: vi.fn(),
  fetchMySignatureImageBlob: vi.fn(),
  exportPdf: api.exportPdf,
  exportFilteredPdfs: api.exportFilteredPdfs,
  finalizeMinute: vi.fn(),
  getAudit: api.getAudit,
  getMinute: api.getMinute,
  getSignatureImage: vi.fn(),
  getMySignatureProfile: api.getMySignatureProfile,
  getSignContext: vi.fn(),
  listComiteEticaMembers: api.listComiteEticaMembers,
  listMinutes: api.listMinutes,
  pendingSignatures: vi.fn(),
  refuseMinute: vi.fn(),
  searchDirectoryUsers: vi.fn(),
  sendForSignature: vi.fn(),
  setSigners: vi.fn(),
  signMinute: vi.fn(),
  updateComiteEticaMember: vi.fn(),
  updateMinute: vi.fn(),
  updateMySignatureProfile: vi.fn(),
  uploadMySignatureImage: vi.fn(),
}));

vi.mock("../hooks/useCecRouterPath", () => ({
  navigateCec: navigation.navigateCec,
}));

const access: ComiteEticaAccess = {
  admin: false,
  can_view: true,
  can_manage: true,
  can_sign: true,
  units: [
    {
      id: "00",
      label: "Comitê de Ética e Conduta",
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
      clearRect: vi.fn(),
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
  api.createVersion.mockResolvedValue({ minute: { id: "minute-1" } });
  api.deleteMinute.mockResolvedValue({ minute: { id: "minute-1" } });
  api.listMinutes.mockResolvedValue({
    items: [
      {
        id: "minute-1",
        unit_code: "00",
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
  api.listComiteEticaMembers.mockResolvedValue([
    {
      id: "member-1",
      unit_code: "00",
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
  api.exportFilteredPdfs.mockResolvedValue(new Blob(["zip"], { type: "application/zip" }));
  api.getMinute.mockResolvedValue({
    minute: {
      id: "minute-1",
      unit_code: "00",
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

describe("CecAppShell compartilhado", () => {
  it("renderiza header, filtros e DataTable navegável na lista", async () => {
    const { container } = render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    expect(screen.getByRole("heading", { name: "Comitê de Ética e Conduta" })).toBeTruthy();
    expect(screen.getByText("DELPI · Ética e Conduta")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Atas" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Nova ata" })).toBeTruthy();
    expect(screen.getByLabelText("Status")).toBeTruthy();
    expect(screen.getByLabelText("Busca")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Buscar$/ })).toBeNull();
    expect(screen.getByRole("button", { name: /Baixar PDFs filtrados/ })).toBeTruthy();

    await screen.findByText("Reunião ordinária");
    const table = container.querySelector(".delpi-ui-table");
    const row = container.querySelector(".delpi-ui-table__row--clickable");
    expect(table).toBeTruthy();
    expect(row).toBeTruthy();
    expect(screen.queryByRole("columnheader", { name: "Nº" })).toBeNull();
    expect(container.querySelector(".dashboard-comite-etica-conduta--minute-list")).toBeTruthy();
    expect(container.querySelector(".cec-minute-list-card")).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Editar$/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /^Excluir$/ })).toBeTruthy();

    fireEvent.keyDown(row!, { key: "Enter" });
    expect(navigation.navigateCec).toHaveBeenCalledWith(
      "/apps/comite-etica-conduta/atas/minute-1",
    );
  });

  it("aplica busca automaticamente sem botão Buscar", async () => {
    render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByText("Reunião ordinária");
    api.listMinutes.mockClear();

    fireEvent.change(screen.getByLabelText("Busca"), {
      target: { value: "ordinária" },
    });

    await waitFor(
      () =>
        expect(api.listMinutes).toHaveBeenCalledWith(
          expect.objectContaining({
            unit_code: "00",
            q: "ordinária",
          }),
          expect.anything(),
        ),
      { timeout: 1500 },
    );
  });

  it("ordena atas pela data mais recente antes de renderizar", async () => {
    api.listMinutes.mockResolvedValue({
      items: [
        {
          id: "older",
          unit_code: "00",
          title: "Ata antiga",
          minute_number: "2026/001",
          meeting_type: "ordinary",
          meeting_date: "2026-05-08",
          status: "draft",
        },
        {
          id: "newer",
          unit_code: "00",
          title: "Ata recente",
          minute_number: "2026/002",
          meeting_type: "ordinary",
          meeting_date: "2026-07-16",
          status: "draft",
        },
      ],
      total: 2,
    });

    render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    const recent = await screen.findByText("Ata recente");
    const old = screen.getByText("Ata antiga");
    expect(
      recent.compareDocumentPosition(old) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("edita e exclui rascunho pela listagem com confirmação", async () => {
    render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByText("Reunião ordinária");
    fireEvent.click(screen.getByRole("button", { name: /^Editar$/ }));
    expect(navigation.navigateCec).toHaveBeenCalledWith(
      "/apps/comite-etica-conduta/atas/minute-1/edit",
    );

    fireEvent.click(screen.getByRole("button", { name: /^Excluir$/ }));
    expect(screen.getByRole("heading", { name: "Excluir ata" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Excluir ata" }));

    await waitFor(() => expect(api.deleteMinute).toHaveBeenCalledWith("minute-1"));
  });

  it("editar ata parcialmente assinada apenas navega, sem criar versão antes de salvar", async () => {
    api.listMinutes.mockResolvedValue({
      items: [
        {
          id: "minute-1",
          unit_code: "00",
          title: "Ata parcialmente assinada",
          minute_number: "ATA-001",
          meeting_type: "ordinary",
          meeting_date: "2026-07-16",
          status: "partially_signed",
          signatures_done: 1,
          signatures_pending: 1,
        },
      ],
      total: 1,
    });

    render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByText("Ata parcialmente assinada");
    fireEvent.click(screen.getByRole("button", { name: /^Editar$/ }));

    await waitFor(() =>
      expect(navigation.navigateCec).toHaveBeenCalledWith(
        "/apps/comite-etica-conduta/atas/minute-1/edit",
      ),
    );
    expect(api.createVersion).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: /^Excluir$/ })).toBeTruthy();
  });

  it("renderiza estado de acesso negado pelo componente canônico", () => {
    const { container } = render(
      <CecAppShell
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
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Membros" }));
    expect(navigation.navigateCec).toHaveBeenCalledWith("/apps/comite-etica-conduta/membros");
  });

  it("renderiza a gestão de membros com composição ativa", async () => {
    render(
      <CecAppShell
        route={{ kind: "members", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByRole("heading", { name: "Comitê de Ética e Conduta" });
    expect(await screen.findByText("Ana Presidente")).toBeTruthy();
    expect(api.listComiteEticaMembers).toHaveBeenCalled();
  });

  it("carrega o fluxo básico da assinatura pessoal", async () => {
    render(
      <CecAppShell
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

  it("baixa ZIP com PDFs das atas filtradas", async () => {
    render(
      <CecAppShell
        route={{ kind: "list", unitCode: "00" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByText("Reunião ordinária");
    fireEvent.click(screen.getByRole("button", { name: /Baixar PDFs filtrados/ }));

    await waitFor(() =>
      expect(api.exportFilteredPdfs).toHaveBeenCalledWith({
        unit_code: "00",
        status: undefined,
        q: undefined,
      }),
    );
  });

  it("renderiza modo de leitura e baixa o PDF oficial", async () => {
    render(
      <CecAppShell
        route={{ kind: "detail", unitCode: "00", minuteId: "minute-1" }}
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

  it("mostra Assinar apenas quando o viewer ainda pode assinar", async () => {
    const detail = {
      minute: {
        id: "minute-1",
        unit_code: "00",
        title: "Reunião ordinária",
        minute_number: "2026/001",
        meeting_type: "ordinary",
        meeting_date: "2026-07-16",
        status: "partially_signed",
      },
      version: { body_html: "<p>Documento da ata.</p>", content_hash: "hash" },
      participants: [],
      signers: [],
      signatures: [],
      action_items: [],
      versions: [],
    };

    api.getMinute.mockResolvedValue({
      ...detail,
      viewer: { user_id: "u1", is_signer: true, has_signed: false, can_sign_now: true },
    });
    const { unmount } = render(
      <CecAppShell
        route={{ kind: "detail", unitCode: "00", minuteId: "minute-1" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );
    expect(await screen.findByRole("button", { name: /Assinar/ })).toBeTruthy();
    unmount();

    api.getMinute.mockResolvedValue({
      ...detail,
      viewer: { user_id: "u1", is_signer: true, has_signed: true, can_sign_now: false },
    });
    render(
      <CecAppShell
        route={{ kind: "detail", unitCode: "00", minuteId: "minute-1" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );
    await screen.findByLabelText("Modo de leitura da ata");
    expect(screen.queryByRole("button", { name: /Assinar/ })).toBeNull();
  });

  it("histórico da ata usa timeline em árvore com branches de auditoria", async () => {
    api.getMinute.mockResolvedValue({
      minute: {
        id: "minute-1",
        unit_code: "00",
        title: "Reunião ordinária",
        minute_number: "2026/001",
        meeting_type: "ordinary",
        meeting_date: "2026-07-16",
        status: "in_review",
      },
      version: { body_html: "<p>Documento da ata.</p>", content_hash: "hash" },
      participants: [],
      signers: [],
      signatures: [],
      action_items: [],
      versions: [
        {
          id: "v1",
          version_number: 1,
          created_at: "2026-07-16T18:26:24-03:00",
          change_reason: "Criação inicial",
        },
      ],
    });
    api.getAudit.mockResolvedValue({
      items: [
        {
          id: "a1",
          action: "sign",
          created_at: "2026-07-16T18:45:52-03:00",
          actor_name: "Robério Oliveira",
          actor_email: "roberio@delpi.com.br",
        },
      ],
    });

    const { container } = render(
      <CecAppShell
        route={{ kind: "detail", unitCode: "00", minuteId: "minute-1" }}
        access={access}
        accessLoading={false}
        accessError={null}
      />,
    );

    await screen.findByText("Versão 1");
    expect(screen.getByText("Assinatura registrada")).toBeTruthy();
    expect(screen.getByText("Robério Oliveira · roberio@delpi.com.br")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-timeline--tree")).toBeTruthy();
    expect(container.querySelector('[data-branch-key="audit"]')).toBeTruthy();
    expect(container.querySelector(".delpi-ui-timeline__marker svg")).toBeTruthy();
  });
});
