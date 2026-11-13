import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LnfPermissionsProvider } from "../../application/LnfPermissionsContext";
import * as api from "../../data/api/invoicePostingApi";
import * as meApi from "../../data/api/meApi";
import type { InvoicePostingRequest } from "../../domain/types";
import { LnfRealtimeProvider } from "../../realtime/LnfRealtimeProvider";
import { QueuePage } from "./QueuePage";

const listeners = new Set<(raw: string) => void>();
const subscribeMock = vi.fn();
const startMock = vi.fn();

vi.mock("../../data/api/meApi");
vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  RealtimeStatusIndicator: () => null,
  ConcurrentChangeNotice: () => null,
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
    // expose flush for the test via module-level helper
    (globalThis as { __lnfFlush?: (events: unknown[]) => void }).__lnfFlush =
      onEvent;
    return { status: enabled ? "open" : "idle" };
  },
  RealtimeSocketClient: class {
    start() {
      startMock();
    }
    stop() {}
    subscribe() {}
    unsubscribe() {}
    getStatus() {
      return "open";
    }
    onStatusChange() {
      return () => undefined;
    }
    addMessageListener(listener: (raw: string) => void) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    }
  },
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

const sample: InvoicePostingRequest = {
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
  created_at: "2026-07-02T10:00:00+00:00",
  updated_at: "2026-07-02T10:00:00+00:00",
};

afterEach(() => {
  cleanup();
  listeners.clear();
  subscribeMock.mockClear();
  startMock.mockClear();
  delete (globalThis as { __lnfFlush?: unknown }).__lnfFlush;
});

beforeEach(() => {
  vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
    id: "u1",
    name: "User",
    email: "u@delpi",
    permissions: [
      "lancamento-notas-fiscais.create",
      "lancamento-notas-fiscais.view",
      "lancamento-notas-fiscais.process",
    ],
  });
  vi.mocked(api.refreshReconciliation).mockResolvedValue({
    status: "skipped",
    updated: 0,
  });
  vi.mocked(api.listRequests).mockResolvedValue({
    items: [sample],
    total: 1,
    page: 1,
    page_size: 20,
    total_pages: 1,
  });
});

describe("QueuePage realtime", () => {
  it("N eventos → 0 POST refresh por evento e ≤ 1 GET extra na janela", async () => {
    render(
      <LnfPermissionsProvider>
        <LnfRealtimeProvider getAccessToken={() => "tok"}>
          <QueuePage
            branch="01"
            onCreate={() => undefined}
            onOpen={() => undefined}
          />
        </LnfRealtimeProvider>
      </LnfPermissionsProvider>,
    );

    await waitFor(() => expect(api.listRequests).toHaveBeenCalled());
    const listCallsAfterMount = vi.mocked(api.listRequests).mock.calls.length;
    const refreshCallsAfterMount =
      vi.mocked(api.refreshReconciliation).mock.calls.length;

    const flush = (globalThis as { __lnfFlush?: (events: unknown[]) => void })
      .__lnfFlush;
    expect(flush).toBeTypeOf("function");
    flush?.(
      Array.from({ length: 5 }, (_, i) => ({
        type: "lnf.request.changed",
        eventId: `e-${i}`,
        branch: "01",
        requestId: "req-1",
        reason: "updated",
      })),
    );

    await waitFor(() =>
      expect(vi.mocked(api.listRequests).mock.calls.length).toBeGreaterThan(
        listCallsAfterMount,
      ),
    );

    expect(
      vi.mocked(api.refreshReconciliation).mock.calls.length,
    ).toBe(refreshCallsAfterMount);
    expect(
      vi.mocked(api.listRequests).mock.calls.length - listCallsAfterMount,
    ).toBeLessThanOrEqual(1);

    const lastFilters =
      vi.mocked(api.listRequests).mock.calls.at(-1)?.[0] ?? {};
    expect(lastFilters).toMatchObject({
      page: 1,
      page_size: 20,
      status: "open",
      branch: "01",
    });
  });
});
