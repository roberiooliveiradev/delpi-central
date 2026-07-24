import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LnfPermissionsProvider } from "../../application/LnfPermissionsContext";
import { QueuePage } from "./QueuePage";
import * as meApi from "../../data/api/meApi";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingRequest } from "../../domain/types";

vi.mock("../../data/api/meApi");
vi.mock("../../data/api/invoicePostingApi");

const sample: InvoicePostingRequest = {
  id: "req-1",
  branch_code: "01",
  document_number: "00123456",
  document_match_key: "000123456",
  series: "1",
  supplier_code: "000001",
  supplier_store: "01",
  supplier_name: "Alpha",
  supplier_short_name: "Alpha",
  issue_date: "2026-07-01",
  amount: 100,
  received_at: "2026-07-02T10:00:00+00:00",
  observation: null,
  status: "pending",
  block_reason: null,
  block_description: null,
  created_by_user_id: "u1",
  created_by_name: "Criador",
  assignee_user_id: null,
  assignee_name: null,
  cancelled_at: null,
  cancelled_by_user_id: null,
  cancelled_by_name: null,
  cancel_justification: null,
  completion_source: null,
  sf1_recno: null,
  erp_entry_date: null,
  reconciled_at: null,
  divergence_alert: false,
  divergence_detected_at: null,
  divergence_detail: null,
  created_at: "2026-07-02T10:00:00+00:00",
  updated_at: "2026-07-02T10:00:00+00:00",
};

const posted = { ...sample, status: "posted" as const, completion_source: "auto" };

function renderQueue(branch: "01" | "02" = "01") {
  return render(
    <LnfPermissionsProvider>
      <QueuePage
        branch={branch}
        onCreate={() => undefined}
        onOpen={() => undefined}
      />
    </LnfPermissionsProvider>,
  );
}

beforeEach(() => {
  vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
    id: "u1",
    name: "User",
    email: "u@delpi",
    permissions: ["lancamento-notas-fiscais.create", "lancamento-notas-fiscais.view"],
  });
  vi.mocked(api.refreshReconciliation).mockResolvedValue({
    status: "skipped",
    updated: 0,
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("QueuePage", () => {
  it("renderiza fila carregada da API sem bloquear pela conciliação", async () => {
    let resolveRefresh: (value: api.ReconciliationRefreshResult) => void = () => undefined;
    vi.mocked(api.refreshReconciliation).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [sample],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
    });
    renderQueue();
    expect(screen.getByTestId("queue-loading")).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByTestId("queue-row-req-1")).toBeTruthy();
    });
    expect(screen.getByTestId("queue-syncing").textContent).toMatch(/Verificando/i);
    expect(screen.getByTestId("queue-context-bar")).toBeTruthy();
    resolveRefresh({ status: "skipped", updated: 0 });
    await waitFor(() => {
      expect(screen.getByTestId("queue-syncing").textContent).toMatch(/Atualizada/i);
    });
    expect(api.refreshReconciliation).toHaveBeenCalledTimes(1);
    expect(
      screen.getAllByTestId("status-badge")[0].textContent,
    ).toContain("Aguardando lançamento");
    expect(screen.getByTestId("btn-new-request")).toBeTruthy();
  });

  it("estado vazio sem filtros orienta cadastro", async () => {
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
    renderQueue();
    await waitFor(() => {
      expect(screen.getByTestId("queue-empty").textContent).toMatch(
        /Nenhuma solicitação cadastrada/i,
      );
    });
    expect(screen.getByTestId("btn-empty-create")).toBeTruthy();
  });

  it("estado vazio com filtros oferecea limpar", async () => {
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
    renderQueue();
    await waitFor(() => expect(api.listRequests).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "posted" } });
    await waitFor(() => {
      expect(screen.getByTestId("filters-active")).toBeTruthy();
    });
    await waitFor(() => {
      expect(screen.getByTestId("queue-empty").textContent).toMatch(
        /Nenhuma solicitação encontrada/i,
      );
    });
    expect(screen.getByTestId("btn-clear-empty-filters")).toBeTruthy();
  });

  it("solicita conciliação na abertura e recarrega após updated", async () => {
    vi.mocked(api.refreshReconciliation).mockResolvedValue({
      status: "completed",
      updated: 1,
    });
    vi.mocked(api.listRequests)
      .mockResolvedValueOnce({
        items: [sample],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      })
      .mockResolvedValueOnce({
        items: [posted],
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      });
    renderQueue();
    await waitFor(() => {
      expect(api.refreshReconciliation).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(screen.getByTestId("queue-sync-notice").textContent).toMatch(
        /atualizada/i,
      );
    });
    expect(vi.mocked(api.listRequests).mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("skipped não exibe erro", async () => {
    vi.mocked(api.refreshReconciliation).mockResolvedValue({
      status: "skipped",
      updated: 0,
    });
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [sample],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
    });
    renderQueue();
    await waitFor(() => expect(screen.getByTestId("queue-row-req-1")).toBeTruthy());
    await waitFor(() => expect(api.refreshReconciliation).toHaveBeenCalled());
    expect(screen.queryByTestId("queue-sync-notice")).toBeNull();
    expect(screen.queryByTestId("queue-error")).toBeNull();
  });

  it("falha de conciliação mantém a fila utilizável", async () => {
    vi.mocked(api.refreshReconciliation).mockResolvedValue({
      status: "failed",
      updated: 0,
    });
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [sample],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
    });
    renderQueue();
    await waitFor(() => expect(screen.getByTestId("queue-row-req-1")).toBeTruthy());
    await waitFor(() => {
      expect(screen.getByTestId("queue-sync-notice").textContent).toMatch(
        /Protheus/i,
      );
    });
    expect(screen.getByTestId("queue-row-req-1")).toBeTruthy();
  });

  it("não repete conciliação ao alterar filtros ou paginação", async () => {
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [sample],
      page: 1,
      page_size: 20,
      total: 40,
      total_pages: 2,
    });
    renderQueue();
    await waitFor(() => expect(api.refreshReconciliation).toHaveBeenCalledTimes(1));
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "posted" } });
    await waitFor(() => {
      expect(api.listRequests).toHaveBeenCalledWith(
        expect.objectContaining({ status: "posted", branch: "01", page: 1 }),
        expect.anything(),
      );
    });
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() => {
      expect(api.listRequests).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
        expect.anything(),
      );
    });
    expect(api.refreshReconciliation).toHaveBeenCalledTimes(1);
  });

  it("não aplica atualização tardia após desmontar", async () => {
    let resolveRefresh: (value: api.ReconciliationRefreshResult) => void = () => undefined;
    vi.mocked(api.refreshReconciliation).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveRefresh = resolve;
        }),
    );
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [sample],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
    });
    const view = renderQueue();
    await waitFor(() => expect(screen.getByTestId("queue-row-req-1")).toBeTruthy());
    view.unmount();
    resolveRefresh({ status: "completed", updated: 1 });
    await Promise.resolve();
    expect(api.listRequests).toHaveBeenCalledTimes(1);
  });

  it("mostra 403 amigável", async () => {
    const { ApiError } = await import("../../data/api/httpClient");
    vi.mocked(api.listRequests).mockRejectedValue(
      new ApiError("Sem permissão", { status: 403, code: "FORBIDDEN" }),
    );
    renderQueue();
    await waitFor(() => {
      expect(screen.getByTestId("queue-error").textContent).toMatch(/permissão/i);
    });
  });
});
