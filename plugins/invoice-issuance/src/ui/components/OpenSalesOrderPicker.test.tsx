import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OpenSalesOrderPicker } from "./OpenSalesOrderPicker";
import * as api from "../../data/api/invoiceIssuanceApi";

vi.mock("../../data/api/invoiceIssuanceApi");
vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("OpenSalesOrderPicker", () => {
  it("mostra vazio quando o cliente não tem PV nesta filial", async () => {
    vi.mocked(api.listOpenSalesOrders).mockResolvedValue({
      orders: [],
      orders_count: 0,
      lines_count: 0,
    });
    render(
      <OpenSalesOrderPicker
        branch="01"
        partyCode="000001"
        partyStore="01"
        onApply={() => undefined}
      />,
    );
    await waitFor(() => expect(screen.getByTestId("open-sales-orders-empty")).toBeTruthy());
  });

  it("aplica linhas marcadas com quantidade limitada ao saldo", async () => {
    vi.mocked(api.listOpenSalesOrders).mockResolvedValue({
      orders_count: 1,
      lines_count: 1,
      orders: [
        {
          sales_order: "000111",
          customer_order_number: "PC-9",
          branch_code: "01",
          lines_count: 1,
          open_quantity: 6,
          open_amount: 75,
          lines: [
            {
              sales_order: "000111",
              sales_order_item: "01",
              customer_order_number: "PC-9",
              product_code: "90260001",
              product_description: "Conector",
              quantity_ordered: 10,
              quantity_delivered: 4,
              quantity_open: 6,
              unit_price: 12.5,
              open_amount: 75,
              stock_on_hand: 20,
            },
          ],
        },
      ],
    });
    const onApply = vi.fn();
    render(
      <OpenSalesOrderPicker
        branch="01"
        partyCode="000001"
        partyStore="01"
        onApply={onApply}
      />,
    );
    await waitFor(() => expect(screen.getByText("PV 000111")).toBeTruthy());
    expect(screen.getByText("6,000")).toBeTruthy();
    expect((screen.getByLabelText("Quantidade a faturar 90260001") as HTMLInputElement).value).toBe(
      "6,000",
    );
    fireEvent.click(screen.getByLabelText("Linha 01"));
    const qty = screen.getByLabelText("Quantidade a faturar 90260001") as HTMLInputElement;
    fireEvent.change(qty, { target: { value: "99" } });
    fireEvent.click(screen.getByText("Usar itens marcados"));
    expect(onApply).toHaveBeenCalledTimes(1);
    expect(onApply.mock.calls[0][0][0].quantity).toBe(6);
    expect(onApply.mock.calls[0][0][0].sales_order).toBe("000111");
    expect(onApply.mock.calls[0][0][0].stock_write_off).toBe(true);
  });
});
