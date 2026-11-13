import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingDetail } from "../../domain/types";
import { LnfRealtimeProvider } from "../../realtime/LnfRealtimeProvider";
import { RequestFormPage } from "./RequestFormPage";

vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
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
  }: {
    enabled: boolean;
    onEvent: (events: unknown[]) => void;
  }) => {
    (globalThis as { __lnfFlush?: (events: unknown[]) => void }).__lnfFlush =
      onEvent;
    return { status: enabled ? "open" : "idle" };
  },
  RealtimeSocketClient: class {
    start() {}
    stop() {}
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
  RealtimeStatusIndicator: () => null,
  FilePreviewModal: () => null,
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

const detail: InvoicePostingDetail = {
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
    observation: "obs original",
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
  },
  history: [],
  comments: [],
  allowed_actions: ["edit"],
  danfe: null,
  xml_original: null,
  xml_standard: null,
  dacte: null,
};

afterEach(() => {
  cleanup();
  delete (globalThis as { __lnfFlush?: unknown }).__lnfFlush;
});

beforeEach(() => {
  vi.mocked(api.getRequest).mockResolvedValue(detail);
});

describe("RequestFormPage realtime", () => {
  it("evento não sobrescreve o digitado; Recarregar aplica o servidor", async () => {
    render(
      <LnfRealtimeProvider getAccessToken={() => "tok"}>
        <RequestFormPage
          mode="edit"
          requestId="req-1"
          lockedBranch="01"
          onCancel={() => undefined}
          onSuccess={() => undefined}
        />
      </LnfRealtimeProvider>,
    );

    await waitFor(() =>
      expect(screen.getByTestId("request-form-page")).toBeTruthy(),
    );
    const observation = screen.getByLabelText("Observação") as HTMLTextAreaElement;
    fireEvent.change(observation, { target: { value: "texto local" } });
    expect(observation.value).toBe("texto local");

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
    expect(observation.value).toBe("texto local");

    vi.mocked(api.getRequest).mockResolvedValue({
      ...detail,
      request: { ...detail.request, observation: "obs do servidor" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Recarregar" }));

    await waitFor(() => expect(observation.value).toBe("obs do servidor"));
  });
});
