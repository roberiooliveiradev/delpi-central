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
const detailMock = vi.fn();
const finalizeMock = vi.fn();
const submitMock = vi.fn();
const decisionMock = vi.fn();
const clarifyMock = vi.fn();
const closingMock = vi.fn();
let manageCap = false;

vi.mock("../../api/packagesApi", () => ({
  listPackages: (...args: unknown[]) => listMock(...args),
  getPackage: (...args: unknown[]) => detailMock(...args),
  finalizePackage: (...args: unknown[]) => finalizeMock(...args),
  submitPackageForReview: (...args: unknown[]) => submitMock(...args),
  reopenPackageVersion: vi.fn(),
  createPackageComplement: vi.fn(),
  createReviewAssignment: vi.fn(),
  deactivateReviewAssignment: vi.fn(),
  recordReviewDecision: (...args: unknown[]) => decisionMock(...args),
  openClarification: (...args: unknown[]) => clarifyMock(...args),
  resolveClarification: vi.fn(),
  confirmTerminalRejection: vi.fn(),
  revertTerminalRejection: vi.fn(),
  getMonthlyClosingState: (...args: unknown[]) => closingMock(...args),
  getClosingCockpit: vi.fn(),
}));

vi.mock("../../app/ViewerContext", () => ({
  useViewerCapabilities: () => ({ access: true, manage: manageCap }),
}));

import { PackagesPage } from "./PackagesPage";

function pkg(overrides: Record<string, unknown> = {}) {
  return {
    package_id: "pkg-1",
    recipient_area: "CONTABIL",
    state: "PACKAGE_INCOMPLETE",
    review_state: "REVIEW_PENDING",
    current_version: null,
    required_areas: [],
    area_decisions: {},
    open_clarifications: 0,
    assignments: [],
    blockers: [],
    revision: 1,
    ...overrides,
  };
}

function submittedPkg() {
  return pkg({
    state: "PACKAGE_SUBMITTED_FOR_REVIEW",
    review_state: "REVIEW_IN_PROGRESS",
    current_version: {
      package_version_id: "pv-1",
      package_id: "pkg-1",
      version_no: 1,
      status: "SUBMITTED",
      content: {},
      required_areas: ["CONTABIL"],
      previous_version_id: null,
      change_reason: null,
      finalized_by: "ana",
      finalized_at: new Date().toISOString(),
      submitted_by: "ana",
      submitted_at: new Date().toISOString(),
      revision: 1,
      created_by: "ana",
      created_at: new Date().toISOString(),
    },
    required_areas: ["CONTABIL"],
    versions: [],
  });
}

function closing(state = "PENDING", blockers: string[] = []) {
  return {
    period: "2026-10",
    state,
    blocking_reasons: blockers,
    packages: [],
    terminal_rejection: null,
  };
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  manageCap = false;
});

describe("PackagesPage", () => {
  it("lista pacotes por destinatário com estado real", async () => {
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [pkg()],
    });
    closingMock.mockResolvedValue(closing());
    render(<PackagesPage />);
    await waitFor(() =>
      expect(screen.getByText("Contábil")).toBeTruthy(),
    );
    expect(screen.getByText("Pacote incompleto")).toBeTruthy();
    expect(listMock).toHaveBeenCalled();
  });

  it("mostra razões de bloqueio da conclusão — sem falso verde", async () => {
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [pkg()],
    });
    closingMock.mockResolvedValue(
      closing("PENDING", ["Package CONTABIL not submitted"]),
    );
    render(<PackagesPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Package CONTABIL not submitted"),
      ).toBeTruthy(),
    );
    expect(screen.getByText("Fechamento pendente")).toBeTruthy();
  });

  it("ações de ciclo de vida exigem manage", async () => {
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [pkg()],
    });
    closingMock.mockResolvedValue(closing());
    detailMock.mockResolvedValue(pkg());
    render(<PackagesPage />);
    await waitFor(() =>
      expect(screen.getByText("Contábil")).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Detalhes" }));
    await waitFor(() =>
      expect(detailMock).toHaveBeenCalled(),
    );
    expect(
      screen.queryByRole("button", { name: "Finalizar pacote" }),
    ).toBeNull();
  });

  it("manage finaliza pacote por destinatário", async () => {
    manageCap = true;
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [pkg()],
    });
    closingMock.mockResolvedValue(closing());
    detailMock.mockResolvedValue(pkg());
    finalizeMock.mockResolvedValue(pkg({ state: "PACKAGE_FINALIZED" }));
    render(<PackagesPage />);
    await waitFor(() =>
      expect(screen.getByText("Contábil")).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Detalhes" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Finalizar pacote" }),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Finalizar pacote" }),
    );
    await waitFor(() =>
      expect(finalizeMock).toHaveBeenCalledWith(
        expect.any(String),
        "CONTABIL",
      ),
    );
  });

  it("envio para análise é ação distinta do finalize", async () => {
    manageCap = true;
    const finalized = pkg({
      state: "PACKAGE_FINALIZED",
      current_version: {
        package_version_id: "pv-1",
        package_id: "pkg-1",
        version_no: 1,
        status: "FINALIZED",
        content: {},
        required_areas: ["CONTABIL"],
        previous_version_id: null,
        change_reason: null,
        finalized_by: "ana",
        finalized_at: new Date().toISOString(),
        submitted_by: null,
        submitted_at: null,
        revision: 2,
        created_by: "ana",
        created_at: new Date().toISOString(),
      },
    });
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [finalized],
    });
    closingMock.mockResolvedValue(closing());
    detailMock.mockResolvedValue(finalized);
    submitMock.mockResolvedValue(submittedPkg());
    render(<PackagesPage />);
    await waitFor(() =>
      expect(screen.getByText("Contábil")).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Detalhes" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Enviar para análise" }),
      ).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar para análise" }),
    );
    await waitFor(() =>
      expect(submitMock).toHaveBeenCalledWith(
        expect.any(String),
        "pv-1",
        2,
      ),
    );
  });

  it("decisão de área registra outcome com motivo", async () => {
    const submitted = submittedPkg();
    listMock.mockResolvedValue({
      period: "2026-10",
      applicable_areas: ["CONTABIL"],
      packages: [submitted],
    });
    closingMock.mockResolvedValue(closing());
    detailMock.mockResolvedValue(submitted);
    decisionMock.mockResolvedValue({});
    render(<PackagesPage />);
    await waitFor(() =>
      expect(screen.getByText("Contábil")).toBeTruthy(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Detalhes" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Área da decisão")).toBeTruthy(),
    );
    fireEvent.change(screen.getByLabelText("Área da decisão"), {
      target: { value: "CONTABIL" },
    });
    fireEvent.change(screen.getByLabelText("Resultado da revisão"), {
      target: { value: "ACCEPTED" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Registrar decisão" }),
    );
    await waitFor(() =>
      expect(decisionMock).toHaveBeenCalledWith(
        expect.any(String),
        "pv-1",
        { area: "CONTABIL", outcome: "ACCEPTED", note: undefined },
      ),
    );
  });
});
