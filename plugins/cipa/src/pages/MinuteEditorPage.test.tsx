// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MinuteEditorPage } from "./MinuteEditorPage";

const api = vi.hoisted(() => ({
  listCipaMembers: vi.fn(),
  getMinute: vi.fn(),
  searchDirectoryUsers: vi.fn(),
  createMinute: vi.fn(),
  createVersion: vi.fn(),
  updateMinute: vi.fn(),
  setSigners: vi.fn(),
}));

vi.mock("../api/cipaApi", () => api);

vi.mock("../hooks/useCipaRouterPath", () => ({
  navigateCipa: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  api.listCipaMembers.mockResolvedValue([
    {
      id: "m1",
      unit_code: "01",
      user_id: "11111111-1111-1111-1111-111111111111",
      display_name: "Ana Presidente",
      role: "president",
      mandate_start: "2026-01-01",
      is_active: true,
    },
  ]);
  api.searchDirectoryUsers.mockResolvedValue([]);
});

describe("MinuteEditorPage composição CIPA", () => {
  it("pré-carrega membros ativos na nova ata", async () => {
    render(<MinuteEditorPage unitCode="01" />);

    await waitFor(() => {
      expect(api.listCipaMembers).toHaveBeenCalledWith("01", {
        activeOn: expect.any(String),
      });
    });
    expect(screen.getAllByText("Ana Presidente").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Presidente da CIPA").length).toBeGreaterThan(0);
    expect(
      screen.getByRole("button", { name: /Recarregar composição CIPA/ }),
    ).toBeTruthy();
  });

  it("não sobrescreve participantes ao editar ata existente", async () => {
    api.getMinute.mockResolvedValue({
      minute: {
        id: "minute-1",
        title: "Ata existente",
        meeting_type: "ordinary",
        meeting_date: "2026-07-16",
        start_time: null,
        end_time: null,
        location: "",
      },
      version: { body_html: "<p>ok</p>" },
      participants: [
        {
          user_id: "22222222-2222-2222-2222-222222222222",
          display_name: "Snapshot Histórico",
          role_in_meeting: "secretary",
          presence: "present",
          is_external: false,
          must_sign: true,
        },
      ],
      signers: [],
      signatures: [],
      action_items: [],
      versions: [],
    });

    render(<MinuteEditorPage unitCode="01" minuteId="minute-1" />);

    await waitFor(() => {
      expect(screen.getAllByText("Snapshot Histórico").length).toBeGreaterThan(0);
    });
    expect(api.listCipaMembers).not.toHaveBeenCalled();
    expect(screen.queryByText("Ana Presidente")).toBeNull();
    expect(
      screen.queryByRole("button", { name: /Recarregar composição CIPA/ }),
    ).toBeNull();
  });

  it("ata em assinatura: avisa e só cria nova versão ao salvar", async () => {
    api.getMinute.mockResolvedValue({
      minute: {
        id: "minute-1",
        title: "Ata parcialmente assinada",
        meeting_type: "ordinary",
        meeting_date: "2026-07-16",
        status: "partially_signed",
        start_time: null,
        end_time: null,
        location: "",
      },
      version: { body_html: "<p>ok</p>" },
      participants: [
        {
          user_id: "22222222-2222-2222-2222-222222222222",
          display_name: "Snapshot Histórico",
          role_in_meeting: "secretary",
          presence: "present",
          is_external: false,
          must_sign: true,
        },
      ],
      signers: [],
      signatures: [],
      action_items: [],
      versions: [],
    });
    api.createVersion.mockResolvedValue({ minute: { id: "minute-1" } });
    api.updateMinute.mockResolvedValue({ minute: { id: "minute-1" } });
    api.setSigners.mockResolvedValue({});

    render(<MinuteEditorPage unitCode="01" minuteId="minute-1" />);

    await waitFor(() => {
      expect(screen.getAllByText("Snapshot Histórico").length).toBeGreaterThan(0);
    });
    // Aviso visível, mas nenhuma versão criada só por abrir o editor.
    expect(
      screen.getByText(/uma nova versão será criada/),
    ).toBeTruthy();
    expect(api.createVersion).not.toHaveBeenCalled();

    fireEvent.click(screen.getAllByRole("button", { name: /^Salvar ata$/ })[0]);

    await waitFor(() =>
      expect(api.createVersion).toHaveBeenCalledWith("minute-1", {
        change_reason: "Ata reaberta para edição pelo gestor.",
      }),
    );
    await waitFor(() => expect(api.updateMinute).toHaveBeenCalled());
    expect(api.createVersion.mock.invocationCallOrder[0]).toBeLessThan(
      api.updateMinute.mock.invocationCallOrder[0],
    );
  });
});
