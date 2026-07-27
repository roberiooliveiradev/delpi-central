import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RequestDetailPage } from "./RequestDetailPage";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingDetail } from "../../domain/types";

vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  UserDirectoryPicker: ({
    value,
    onChange,
    disabled,
    labels,
  }: {
    value: Array<{ id: string; name: string; email: string }>;
    onChange: (users: Array<{ id: string; name: string; email: string }>) => void;
    disabled?: boolean;
    labels?: { title?: string };
  }) => (
    <div>
      <span>{labels?.title || "Usuários"}</span>
      <button
        type="button"
        disabled={disabled}
        onClick={() =>
          onChange([
            {
              id: "u-compras",
              name: "Compras Delpi",
              email: "compras@delpi.com.br",
            },
          ])
        }
      >
        Selecionar responsável mock
      </button>
      {value[0] ? <span>{value[0].name}</span> : null}
    </div>
  ),
}));

const detail = (actions: InvoicePostingDetail["allowed_actions"]): InvoicePostingDetail => ({
  request: {
    id: "req-1",
    branch_code: "01",
    document_number: "00123456",
    document_match_key: "000123456",
    series: "",
    supplier_code: "000001",
    supplier_store: "01",
    supplier_name: "Alpha",
    supplier_short_name: null,
    issue_date: "2026-07-01",
    amount: 50,
    received_at: "2026-07-02T10:00:00+00:00",
    observation: "obs",
    status: actions.includes("resume") ? "blocked" : "pending",
    block_reason: actions.includes("resume") ? "other" : null,
    block_description: actions.includes("resume") ? "pendência" : null,
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
    linked_po_number: null,
    linked_po_delivery_date: null,
    linked_po_issue_date: null,
    linked_po_open_value: null,
    linked_po_product_count: null,
    linked_po_linked_at: null,
    linked_po_linked_by_user_id: null,
    linked_po_linked_by_name: null,
    created_at: "2026-07-02T10:00:00+00:00",
    updated_at: "2026-07-02T10:00:00+00:00",
  },
  history: [
    {
      id: "h1",
      request_id: "req-1",
      event_type: "created",
      actor_origin: "user",
      actor_user_id: "u1",
      actor_name: "Criador",
      from_status: null,
      to_status: "pending",
      changes: {},
      justification: null,
      created_at: "2026-07-02T10:00:00+00:00",
    },
  ],
  comments: [],
  allowed_actions: actions,
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("RequestDetailPage", () => {
  it("abre detalhes e histórico", async () => {
    vi.mocked(api.getRequest).mockResolvedValue({
      ...detail(["view", "comment"]),
      history: [
        {
          id: "h1",
          request_id: "req-1",
          event_type: "created",
          actor_origin: "user",
          actor_user_id: "u1",
          actor_name: "Criador",
          from_status: null,
          to_status: "pending",
          changes: {},
          justification: null,
          created_at: "2026-07-02T10:00:00+00:00",
        },
        {
          id: "h2",
          request_id: "req-1",
          event_type: "status_changed",
          actor_origin: "user",
          actor_user_id: "u2",
          actor_name: "Fiscal",
          from_status: "in_progress",
          to_status: "blocked",
          changes: {
            assignee_name: { from: "Fiscal", to: "Compras Delpi" },
          },
          justification: "Falta o PC",
          created_at: "2026-07-02T11:00:00+00:00",
        },
      ],
    });
    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    expect(screen.getByText("Solicitação criada")).toBeTruthy();
    expect(screen.getByText("Pendência registrada")).toBeTruthy();
    expect(screen.getByText("Falta o PC")).toBeTruthy();
    expect(screen.getByText("Responsável: Compras Delpi")).toBeTruthy();
    const blockedItem = screen.getByText("Pendência registrada").closest("li");
    expect(blockedItem?.className).toContain("lnf-timeline__item--blocked");
    expect(screen.getByText("Resumo")).toBeTruthy();
    expect(screen.getByText("Dados fiscais")).toBeTruthy();
    expect(screen.getByText("Situação atual")).toBeTruthy();
    expect(screen.getByText("Histórico e comentários")).toBeTruthy();
    expect(screen.queryByTestId("posting-lead-time")).toBeNull();
    expect(screen.queryByText(/R_E_C_N_O_/i)).toBeNull();
    expect(screen.queryByText("req-1")).toBeNull();
    expect(screen.queryByRole("button", { name: "Iniciar atendimento" })).toBeNull();
  });

  it("mostra tempo até lançamento quando postada", async () => {
    const posted = detail(["view"]);
    posted.request.status = "posted";
    posted.request.completion_source = "auto";
    posted.request.reconciled_at = "2026-07-02T14:30:00+00:00";
    vi.mocked(api.getRequest).mockResolvedValue(posted);

    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("posting-lead-time")).toBeTruthy());
    expect(screen.getByTestId("posting-lead-time").textContent).toContain("4h 30min");
  });

  it("mostra ações conforme allowed_actions", async () => {
    vi.mocked(api.getRequest).mockResolvedValue(
      detail(["view", "start", "block", "cancel", "edit", "comment", "post_manual"]),
    );
    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("detail-actions")).toBeTruthy());
    expect(screen.getByRole("button", { name: "Iniciar atendimento" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Bloquear" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Já lançada" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Corrigir" })).toBeTruthy();
  });

  it("mostra vínculo de pedido de compra na situação atual", async () => {
    const withPo = detail(["view", "link_purchase_order"]);
    withPo.request.linked_po_number = "000123";
    withPo.request.linked_po_delivery_date = "2026-07-20";
    withPo.request.linked_po_open_value = 150.5;
    withPo.request.linked_po_product_count = 2;
    withPo.history = [
      ...withPo.history,
      {
        id: "h-po",
        request_id: "req-1",
        event_type: "purchase_order_linked",
        actor_origin: "user",
        actor_user_id: "u-process",
        actor_name: "Processador",
        from_status: "pending",
        to_status: "pending",
        changes: {
          linked_po: {
            from: null,
            to: { order_number: "000123", delivery_date: "2026-07-20" },
          },
        },
        justification: "Pedido amarrado: PC 000123 · entrega 20/07/2026",
        created_at: "2026-07-02T11:00:00+00:00",
      },
    ];
    vi.mocked(api.getRequest).mockResolvedValue(withPo);

    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("linked-po-summary")).toBeTruthy());
    expect(screen.getByTestId("linked-po-summary").textContent).toContain("PC 000123");
    expect(screen.getByText("Pedido de compra amarrado")).toBeTruthy();
    expect(screen.getByText(/Pedido amarrado: PC 000123/)).toBeTruthy();
  });

  it("mostra botão de pedidos de compra", async () => {
    vi.mocked(api.getRequest).mockResolvedValue(detail(["view"]));
    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("btn-purchase-orders")).toBeTruthy());
    expect(screen.getByRole("button", { name: "Incluir Pedido de Compras" })).toBeTruthy();
  });

  it("bloqueia e retoma via API", async () => {
    vi.mocked(api.getRequest)
      .mockResolvedValueOnce(detail(["view", "block"]))
      .mockResolvedValueOnce(detail(["view", "resume"]))
      .mockResolvedValue(detail(["view"]));
    vi.mocked(api.blockRequest).mockResolvedValue({} as never);
    vi.mocked(api.resumeRequest).mockResolvedValue({} as never);

    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => screen.getByRole("button", { name: "Bloquear" }));
    fireEvent.click(screen.getByRole("button", { name: "Bloquear" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Selecionar responsável mock" }));
    fireEvent.change(within(dialog).getByLabelText("Descrição"), {
      target: { value: "Falta pedido" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Bloquear" }));
    await waitFor(() =>
      expect(api.blockRequest).toHaveBeenCalledWith("req-1", {
        block_reason: "purchase_order",
        block_description: "Falta pedido",
        assignee_user_id: "u-compras",
        assignee_name: "Compras Delpi",
      }),
    );
    await waitFor(() => screen.getByRole("button", { name: "Retomar" }));
    fireEvent.click(screen.getByRole("button", { name: "Retomar" }));
    await waitFor(() => expect(api.resumeRequest).toHaveBeenCalledWith("req-1"));
  });

  it("cancela com justificativa e confirmação", async () => {
    vi.mocked(api.getRequest).mockResolvedValue(detail(["view", "cancel"]));
    vi.mocked(api.cancelRequest).mockResolvedValue({} as never);
    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => screen.getByRole("button", { name: "Cancelar" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    const dialog = await screen.findByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Justificativa"), {
      target: { value: "Digitou errado" },
    });
    fireEvent.click(within(dialog).getByLabelText(/Confirmo o cancelamento/i));
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancelar solicitação" }));
    await waitFor(() =>
      expect(api.cancelRequest).toHaveBeenCalledWith("req-1", "Digitou errado"),
    );
  });

  it("envia comentário", async () => {
    vi.mocked(api.getRequest).mockResolvedValue(detail(["view", "comment"]));
    vi.mocked(api.addComment).mockResolvedValue({
      id: "c1",
      request_id: "req-1",
      author_user_id: "u1",
      author_name: "Criador",
      body: "olá",
      created_at: "2026-07-02T11:00:00+00:00",
    });
    render(
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />,
    );
    await waitFor(() => screen.getByTestId("comment-input"));
    fireEvent.change(screen.getByTestId("comment-input"), {
      target: { value: "  olá  " },
    });
    fireEvent.click(screen.getByRole("button", { name: "Comentar" }));
    await waitFor(() => expect(api.addComment).toHaveBeenCalledWith("req-1", "olá"));
  });
});
