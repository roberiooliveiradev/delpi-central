import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CarrierSearch } from "./CarrierSearch";
import * as api from "../../data/api/invoiceIssuanceApi";

vi.mock("../../data/api/invoiceIssuanceApi");
vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CarrierSearch", () => {
  it("lista transportadoras pelo nome reduzido e permite selecionar", async () => {
    vi.mocked(api.searchCarriers).mockResolvedValue([
      {
        carrier_code: "000001",
        carrier_name: "JADLOG",
        legal_name: "JADLOG LOGISTICA LTDA",
        tax_id: "12345678000199",
        blocked: false,
      },
    ]);
    const onSelect = vi.fn();
    render(<CarrierSearch selected={null} onSelect={onSelect} />);
    fireEvent.change(screen.getByPlaceholderText("Digite ao menos 2 caracteres"), {
      target: { value: "jad" },
    });
    await waitFor(() => expect(screen.getByTestId("carrier-results")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: /000001/ }));
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ carrier_code: "000001", carrier_name: "JADLOG" }),
    );
  });
});
