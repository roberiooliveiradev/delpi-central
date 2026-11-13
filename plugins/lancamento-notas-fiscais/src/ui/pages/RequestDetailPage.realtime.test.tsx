import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingDetail } from "../../domain/types";
import { LnfRealtimeProvider } from "../../realtime/LnfRealtimeProvider";
import { RequestDetailPage } from "./RequestDetailPage";

const subscribeMock = vi.fn();

vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  RealtimeStatusIndicator: () => null,
  ConcurrentChangeNotice: ({
    message,
    onAction,
  }: {
    message: string;
    onAction: () => void;
  }) => (
    <div data-testid="concurrent-change-notice">
      <p>{message}</p>
      <button type="button" onClick={onAction}>
        Recarregar
      </button>
    </div>
  ),
  useRealtimeRooms: ({
    enabled,
    onEvent,
    rooms,
    encodeSubscribe,
  }: {
    enabled: boolean;
    onEvent: (events: unknown[]) => void;
    rooms: string[];
    encodeSubscribe?: (room: string) => string;
  }) => {
    if (enabled) {
      for (const room of rooms) {
        subscribeMock(encodeSubscribe ? encodeSubscribe(room) : room);
      }
    }
    (globalThis as { __lnfFlush?: (events: unknown[]) => void }).__lnfFlush =
      onEvent;
    return { status: enabled ? "open" : "idle" };
  },
  RealtimeSocketClient: class {
    start() {}
    stop() {}
    subscribe() {}
    unsubscribe() {}
    getStatus() {
      return "open";
    }
    onStatusChange() {
      return () => undefined;
    }
    addMessageListener() {
      return () => undefined;
    }
  },
  useFilePreviewLoader: () => ({
    kind: "pdf",
    loading: false,
    error: null,
    previewUrl: null,
    textContent: null,
    textTruncated: false,
    spreadsheetData: null,
    docxData: null,
  }),
  FilePreviewView: () => null,
  UserDirectoryPicker: () => null,
}));

vi.mock("../../realtime/config", async () => {
  const actual = await vi.importActual<typeof import("../../realtime/config")>(
    "../../realtime/config",
  );
  return {
    ...actual,
    shouldConnectLnfRealtime: () => true,
  };
});

const detail = (overrides?: Partial<InvoicePostingDetail["request"]>): InvoicePostingDetail => ({
  request: {
    id: "req-1",
    branch_code: "01",
    document_number: "00123456",
    document_match_key: "000123456",
    series: "1",
    fiscal_model: "nfe",
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
    linked_po_number: null,
    linked_po_delivery_date: null,
    linked_po_issue_date: null,
    linked_po_open_value: null,
    linked_po_product_count: null,
    linked_po_linked_at: null,
    linked_po_linked_by_user_id: null,
    linked_po_linked_by_name: null,
    linked_purchase_orders: [],
    linked_invoices: [],
    created_at: "2026-07-02T10:00:00+00:00",
    updated_at: "2026-07-02T10:00:00+00:00",
    ...overrides,
  },
  history: [],
  comments: [],
  allowed_actions: ["comment", "block"],
  danfe: null,
});

afterEach(() => {
  cleanup();
  subscribeMock.mockClear();
  delete (globalThis as { __lnfFlush?: unknown }).__lnfFlush;
});

beforeEach(() => {
  vi.mocked(api.getRequest).mockResolvedValue(detail());
});

function renderDetail() {
  return render(
    <LnfRealtimeProvider getAccessToken={() => "tok"}>
      <RequestDetailPage
        requestId="req-1"
        onBack={() => undefined}
        onEdit={() => undefined}
      />
    </LnfRealtimeProvider>,
  );
}

describe("RequestDetailPage realtime", () => {
  it("evento → refetch e preserva rascunho de comentário", async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    const callsAfterMount = vi.mocked(api.getRequest).mock.calls.length;

    const input = screen.getByTestId("comment-input");
    fireEvent.change(input, { target: { value: "rascunho vivo" } });
    expect((input as HTMLTextAreaElement | HTMLInputElement).value).toBe(
      "rascunho vivo",
    );

    const flush = (globalThis as { __lnfFlush?: (events: unknown[]) => void })
      .__lnfFlush;
    flush?.([
      {
        type: "lnf.request.changed",
        eventId: "e-1",
        branch: "01",
        requestId: "req-1",
        reason: "updated",
      },
    ]);

    await waitFor(() =>
      expect(screen.getByTestId("concurrent-change-notice")).toBeTruthy(),
    );
    expect(vi.mocked(api.getRequest).mock.calls.length).toBe(callsAfterMount);
    expect((input as HTMLTextAreaElement | HTMLInputElement).value).toBe(
      "rascunho vivo",
    );

    fireEvent.click(screen.getByRole("button", { name: "Recarregar" }));
    await waitFor(() =>
      expect(vi.mocked(api.getRequest).mock.calls.length).toBeGreaterThan(
        callsAfterMount,
      ),
    );
    expect((input as HTMLTextAreaElement | HTMLInputElement).value).toBe(
      "rascunho vivo",
    );
  });

  it("sem rascunho → refetch silencioso sem aviso", async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    const callsAfterMount = vi.mocked(api.getRequest).mock.calls.length;

    const flush = (globalThis as { __lnfFlush?: (events: unknown[]) => void })
      .__lnfFlush;
    flush?.([
      {
        type: "lnf.request.changed",
        eventId: "e-2",
        branch: "01",
        requestId: "req-1",
        reason: "commented",
      },
    ]);

    await waitFor(() =>
      expect(vi.mocked(api.getRequest).mock.calls.length).toBeGreaterThan(
        callsAfterMount,
      ),
    );
    expect(screen.queryByTestId("concurrent-change-notice")).toBeNull();
  });

  it("modal aberto → aviso e aplica ao fechar", async () => {
    renderDetail();
    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    const callsAfterMount = vi.mocked(api.getRequest).mock.calls.length;

    fireEvent.click(screen.getByRole("button", { name: /Bloquear/i }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Cancelar" })).toBeTruthy(),
    );

    const flush = (globalThis as { __lnfFlush?: (events: unknown[]) => void })
      .__lnfFlush;
    flush?.([
      {
        type: "lnf.request.changed",
        eventId: "e-3",
        branch: "01",
        requestId: "req-1",
        reason: "updated",
      },
    ]);

    await waitFor(() =>
      expect(screen.getByTestId("concurrent-change-notice")).toBeTruthy(),
    );
    expect(vi.mocked(api.getRequest).mock.calls.length).toBe(callsAfterMount);

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    await waitFor(() =>
      expect(vi.mocked(api.getRequest).mock.calls.length).toBeGreaterThan(
        callsAfterMount,
      ),
    );
  });
});
