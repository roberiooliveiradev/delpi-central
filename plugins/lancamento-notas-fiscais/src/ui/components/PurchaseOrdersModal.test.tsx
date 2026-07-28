import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PurchaseOrdersModal } from "./PurchaseOrdersModal";
import * as api from "../../data/api/invoicePostingApi";

vi.mock("../../data/api/invoicePostingApi");

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

const sampleGroup = {
  order_number: "000123",
  delivery_date: "2026-07-20",
  issue_date: "2026-07-01",
  product_count: 1,
  open_value: 12,
  item_count: 1,
  items: [
    {
      branch: "01",
      order_number: "000123",
      order_item: "0001",
      product_code: "10080001",
      product_description: "Parafuso",
      supplier_part_number: "FORN-P1",
      warehouse: "01",
      unit: "UN",
      ordered_quantity: 10,
      delivered_quantity: 2,
      open_quantity: 8,
      pre_invoice_quantity: 0,
      issue_date: "2026-07-01",
      expected_delivery_date: "2026-07-20",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      unit_price: 1.5,
      open_merchandise_value: 12,
      open_ipi_value: 0,
      open_freight_value: 0,
      open_discount_value: 0,
      open_value: 12,
    },
  ],
};

const sampleGroupB = {
  ...sampleGroup,
  order_number: "000456",
  delivery_date: "2026-07-25",
  open_value: 30,
  items: [
    {
      ...sampleGroup.items[0],
      order_number: "000456",
      product_code: "20080001",
      product_description: "Porca",
      supplier_part_number: "FORN-B2",
      expected_delivery_date: "2026-07-25",
      open_merchandise_value: 30,
      open_ipi_value: 0,
      open_value: 30,
    },
  ],
};

describe("PurchaseOrdersModal", () => {
  it("lista grupos e permite ver detalhes", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 1,
      group_count: 1,
      item_count: 1,
      groups: [sampleGroup],
      linked: [],
      can_link: true,
    });

    render(
      <PurchaseOrdersModal
        open
        requestId="req-1"
        supplierName="Alpha"
        branchCode="01"
        canLink
        onClose={() => undefined}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("po-table")).toBeTruthy());
    expect(screen.getByText("000123")).toBeTruthy();
    expect(screen.getByText(/1 pedido/)).toBeTruthy();
    expect(screen.getByText(/1 grupo/)).toBeTruthy();
    // Com canLink o primeiro grupo já vem expandido para seleção por linha
    expect(screen.getByText("10080001")).toBeTruthy();
    expect(screen.getByText(/FORN-P1/)).toBeTruthy();
    expect(screen.getByText("Parafuso")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Ocultar" }));
    expect(screen.queryByText("Parafuso")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Ver detalhes" }));
    expect(screen.getByText("Parafuso")).toBeTruthy();
  });

  it("amarra vários grupos selecionados", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 2,
      group_count: 2,
      item_count: 2,
      groups: [sampleGroup, sampleGroupB],
      linked: [],
      can_link: true,
    });
    vi.mocked(api.linkRequestPurchaseOrder).mockResolvedValue({} as never);
    const onLinked = vi.fn();
    const onClose = vi.fn();

    render(
      <PurchaseOrdersModal
        open
        requestId="req-1"
        supplierName="Alpha"
        branchCode="01"
        canLink
        onClose={onClose}
        onLinked={onLinked}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("po-table")).toBeTruthy());
    fireEvent.click(screen.getByLabelText("Selecionar PC 000123"));
    fireEvent.click(screen.getByLabelText("Selecionar PC 000456"));
    fireEvent.click(screen.getByTestId("po-link-btn"));
    await waitFor(() => expect(api.linkRequestPurchaseOrder).toHaveBeenCalled());
    expect(api.linkRequestPurchaseOrder).toHaveBeenCalledWith("req-1", {
      groups: [
        {
          order_number: "000123",
          delivery_date: "2026-07-20",
          lines: [{ order_item: "0001" }],
        },
        {
          order_number: "000456",
          delivery_date: "2026-07-25",
          lines: [{ order_item: "0001" }],
        },
      ],
    });
    expect(onLinked).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it("amarra apenas linhas selecionadas do grupo", async () => {
    const multiItemGroup = {
      ...sampleGroup,
      product_count: 2,
      open_value: 42,
      item_count: 2,
      items: [
        sampleGroup.items[0],
        {
          ...sampleGroup.items[0],
          order_item: "0002",
          product_code: "10080002",
          product_description: "Porca",
          open_merchandise_value: 30,
          open_value: 30,
        },
      ],
    };
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 1,
      group_count: 1,
      item_count: 2,
      groups: [multiItemGroup],
      linked: [],
      can_link: true,
    });
    vi.mocked(api.linkRequestPurchaseOrder).mockResolvedValue({} as never);

    render(
      <PurchaseOrdersModal
        open
        requestId="req-1"
        supplierName="Alpha"
        branchCode="01"
        canLink
        onClose={() => undefined}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("po-table")).toBeTruthy());
    fireEvent.click(
      screen.getByLabelText("Selecionar item 0002 do PC 000123"),
    );
    fireEvent.click(screen.getByTestId("po-link-btn"));
    await waitFor(() => expect(api.linkRequestPurchaseOrder).toHaveBeenCalled());
    expect(api.linkRequestPurchaseOrder).toHaveBeenCalledWith("req-1", {
      groups: [
        {
          order_number: "000123",
          delivery_date: "2026-07-20",
          lines: [{ order_item: "0002" }],
        },
      ],
    });
  });

  it("mostra estado vazio", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 0,
      group_count: 0,
      item_count: 0,
      groups: [],
      linked: [],
      can_link: false,
    });

    render(
      <PurchaseOrdersModal
        open
        requestId="req-1"
        supplierName="Alpha"
        branchCode="01"
        canLink={false}
        onClose={() => undefined}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("po-empty")).toBeTruthy());
    fireEvent.click(screen.getByTestId("po-close-btn"));
  });

  it("filtra por pedido e por código do fornecedor", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 2,
      group_count: 2,
      item_count: 2,
      groups: [sampleGroup, sampleGroupB],
      linked: [],
      can_link: true,
    });

    render(
      <PurchaseOrdersModal
        open
        requestId="req-1"
        supplierName="Alpha"
        branchCode="01"
        canLink
        onClose={() => undefined}
      />,
    );

    await waitFor(() => expect(screen.getByTestId("po-table")).toBeTruthy());
    expect(screen.getByTestId("po-group-000123")).toBeTruthy();
    expect(screen.getByTestId("po-group-000456")).toBeTruthy();

    fireEvent.change(screen.getByTestId("po-filter-input"), {
      target: { value: "000456" },
    });
    expect(screen.queryByTestId("po-group-000123")).toBeNull();
    expect(screen.getByTestId("po-group-000456")).toBeTruthy();
    expect(screen.getByText(/1 no filtro/)).toBeTruthy();

    fireEvent.change(screen.getByTestId("po-filter-input"), {
      target: { value: "FORN-P1" },
    });
    expect(screen.getByTestId("po-group-000123")).toBeTruthy();
    expect(screen.queryByTestId("po-group-000456")).toBeNull();
    expect(screen.getByText(/FORN-P1/)).toBeTruthy();

    fireEvent.change(screen.getByTestId("po-filter-input"), {
      target: { value: "zzz-inexistente" },
    });
    expect(screen.getByTestId("po-filter-empty")).toBeTruthy();
    expect(screen.queryByTestId("po-table")).toBeNull();
  });
});
