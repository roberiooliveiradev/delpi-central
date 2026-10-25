import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listMock = vi.fn();
const historyMock = vi.fn();
const claimMock = vi.fn();
const transitionMock = vi.fn();
const reassignMock = vi.fn();
const confirmClassMock = vi.fn();
let manageCap = false;

vi.mock("../../api/pendenciesApi", () => ({
  listPendencies: (...args: unknown[]) => listMock(...args),
  listPendencyHistory: (...args: unknown[]) => historyMock(...args),
  claimPendency: (...args: unknown[]) => claimMock(...args),
  transitionPendency: (...args: unknown[]) => transitionMock(...args),
  reassignPendency: (...args: unknown[]) => reassignMock(...args),
  confirmPendencyClassification: (...args: unknown[]) =>
    confirmClassMock(...args),
}));

vi.mock("../../app/ViewerContext", () => ({
  useViewerCapabilities: () => ({ access: true, manage: manageCap }),
}));

import { PendenciesPage } from "./PendenciesPage";

function pendency(overrides: Record<string, unknown> = {}) {
  return {
    pendency_id: "p-1",
    competence_id: "comp-1",
    snapshot_item_id: null,
    kind: "MISSING_EVIDENCE",
    title: "Nota fiscal pendente",
    description: null,
    state: "OPEN",
    queue: null,
    responsible_subject: null,
    branch_scope: "BOTH",
    suggested_classification: null,
    suggestion_rationale: null,
    suggestion_source: null,
    confirmed_classification: null,
    classification_reason: null,
    resolution_notes: null,
    dismiss_justification: null,
    revision: 1,
    created_by: "ana",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  manageCap = false;
});

describe("PendenciesPage", () => {
  it("lista pendências da competência vigente", async () => {
    listMock.mockResolvedValue({ items: [pendency()], limit: 50, offset: 0 });
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(screen.getByText("Nota fiscal pendente")).toBeTruthy(),
    );
    expect(listMock).toHaveBeenCalled();
  });

  it("sugestão automática é marcada como recomendação", async () => {
    listMock.mockResolvedValue({
      items: [
        pendency({
          suggested_classification: "RECONCILIATION",
          suggestion_source: "DETERMINISTIC",
        }),
      ],
      limit: 50,
      offset: 0,
    });
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(
        screen.getByText(/sugestão automática/),
      ).toBeTruthy(),
    );
    expect(screen.queryByText(/confirmada/)).toBeNull();
  });

  it("claim atribui responsável sem mudar estado", async () => {
    listMock.mockResolvedValue({ items: [pendency()], limit: 50, offset: 0 });
    claimMock.mockResolvedValue(pendency({ responsible_subject: "ana" }));
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Assumir" }),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Assumir" }));
    await waitFor(() =>
      expect(claimMock).toHaveBeenCalledWith(
        expect.any(String),
        "p-1",
        1,
      ),
    );
  });

  it("descarte exige justificativa no diálogo", async () => {
    listMock.mockResolvedValue({ items: [pendency()], limit: 50, offset: 0 });
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Descartar…" }),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Descartar…" }));
    const submit = await screen.findByRole("button", {
      name: "Confirmar descarte",
    });
    expect(submit).toHaveProperty("disabled", true);
  });

  it("ações governadas (reatribuir/classificar) exigem manage", async () => {
    listMock.mockResolvedValue({ items: [pendency()], limit: 50, offset: 0 });
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(screen.getByText("Nota fiscal pendente")).toBeTruthy(),
    );
    expect(
      screen.queryByRole("button", { name: "Reatribuir…" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", {
        name: "Confirmar classificação…",
      }),
    ).toBeNull();
  });

  it("manage vê ações governadas", async () => {
    manageCap = true;
    listMock.mockResolvedValue({ items: [pendency()], limit: 50, offset: 0 });
    render(<PendenciesPage />);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Reatribuir…" }),
      ).toBeTruthy(),
    );
  });
});
