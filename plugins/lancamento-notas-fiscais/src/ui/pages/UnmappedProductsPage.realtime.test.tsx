import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { LnfPermissionsProvider } from "../../application/LnfPermissionsContext";
import * as api from "../../data/api/invoicePostingApi";
import * as meApi from "../../data/api/meApi";
import type { UnmappedSupplierProduct } from "../../domain/types";
import { LnfRealtimeProvider } from "../../realtime/LnfRealtimeProvider";
import { UnmappedProductsPage } from "./UnmappedProductsPage";

const subscribeMock = vi.fn();

vi.mock("../../data/api/meApi");
vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  RealtimeStatusIndicator: () => null,
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

const row: UnmappedSupplierProduct = {
  id: "row-1",
  request_id: "req-1",
  branch_code: "01",
  supplier_code: "000006",
  supplier_store: "01",
  supplier_name: "Tramar",
  supplier_product_code: "REF-1",
  supplier_product_description: "Parafuso",
  quantity: "4",
  unit: "PC",
  mapping_status: "unmapped",
  document_number: "000012078",
  series: "1",
  created_at: "2026-10-06T12:00:00+00:00",
};

afterEach(() => {
  cleanup();
  subscribeMock.mockClear();
  vi.clearAllMocks();
  delete (globalThis as { __lnfFlush?: unknown }).__lnfFlush;
});

beforeEach(() => {
  vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
    id: "u1",
    name: "Ana",
    email: "ana@delpi",
    permissions: ["lancamento-notas-fiscais.review-unmapped-products"],
    is_superadmin: false,
  });
  vi.mocked(api.listUnmappedProducts).mockResolvedValue({
    items: [row],
    page: 1,
    page_size: 20,
    total: 1,
    total_pages: 1,
  });
});

describe("UnmappedProductsPage realtime", () => {
  it("assina unmapped-products e refetch na página atual", async () => {
    render(
      <LnfPermissionsProvider>
        <LnfRealtimeProvider getAccessToken={() => "tok"}>
          <UnmappedProductsPage />
        </LnfRealtimeProvider>
      </LnfPermissionsProvider>,
    );

    await waitFor(() =>
      expect(subscribeMock).toHaveBeenCalledWith(
        JSON.stringify({ type: "subscribe", room: "lnf:unmapped-products" }),
      ),
    );
    const callsAfterMount = vi.mocked(api.listUnmappedProducts).mock.calls.length;

    const flush = (globalThis as { __lnfFlush?: (events: unknown[]) => void })
      .__lnfFlush;
    flush?.([
      {
        type: "lnf.unmapped-products.changed",
        eventId: "e-1",
      },
    ]);

    await waitFor(() =>
      expect(vi.mocked(api.listUnmappedProducts).mock.calls.length).toBeGreaterThan(
        callsAfterMount,
      ),
    );
    const last = vi.mocked(api.listUnmappedProducts).mock.calls.at(-1)?.[0] ?? {};
    expect(last).toMatchObject({ page: 1, page_size: 20 });
  });

  it("sem permission → zero subscribe", async () => {
    vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
      id: "u2",
      name: "Sem",
      email: "sem@delpi",
      permissions: ["lancamento-notas-fiscais.view"],
      is_superadmin: false,
    });
    render(
      <LnfPermissionsProvider>
        <LnfRealtimeProvider getAccessToken={() => "tok"}>
          <UnmappedProductsPage />
        </LnfRealtimeProvider>
      </LnfPermissionsProvider>,
    );
    await waitFor(() =>
      expect(
        document.body.textContent ?? "",
      ).toMatch(/não tem permissão/i),
    );
    expect(subscribeMock).not.toHaveBeenCalled();
    expect(api.listUnmappedProducts).not.toHaveBeenCalled();
  });
});
