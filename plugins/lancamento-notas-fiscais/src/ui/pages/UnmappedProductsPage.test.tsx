import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LnfPermissionsProvider } from "../../application/LnfPermissionsContext";
import * as api from "../../data/api/invoicePostingApi";
import * as meApi from "../../data/api/meApi";
import type { UnmappedSupplierProduct } from "../../domain/types";
import { UnmappedProductsPage } from "./UnmappedProductsPage";

vi.mock("../../data/api/meApi");
vi.mock("../../data/api/invoicePostingApi");

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
  vi.clearAllMocks();
});

function renderPage() {
  return render(
    <LnfPermissionsProvider>
      <UnmappedProductsPage />
    </LnfPermissionsProvider>,
  );
}

describe("UnmappedProductsPage", () => {
  it("lista produto sem vínculo e o ambíguo", async () => {
    vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
      id: "u1",
      name: "Ana",
      email: "ana@delpi",
      permissions: ["lancamento-notas-fiscais.review-unmapped-products"],
      is_superadmin: false,
    });
    vi.mocked(api.listUnmappedProducts).mockResolvedValue({
      items: [row, { ...row, id: "row-2", supplier_product_code: "REF-2", mapping_status: "ambiguous" }],
      page: 1,
      page_size: 20,
      total: 2,
      total_pages: 1,
    });

    renderPage();

    expect(await screen.findByText("REF-1")).toBeTruthy();
    const table = screen.getByTestId("unmapped-table");
    expect(table.textContent).toContain("REF-2");
    expect(table.textContent).toContain("Sem vínculo");
    expect(table.textContent).toContain("Ambíguo");
    expect(table.textContent).toContain("Tramar");
    const link = table.querySelector("a");
    expect(link?.getAttribute("href")).toBe(
      "/apps/lancamento-notas-fiscais/filial-01?requestId=req-1",
    );
  });

  it("não abre a lista para quem só administra solicitações", async () => {
    vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
      id: "u1",
      name: "Ana",
      email: "ana@delpi",
      permissions: ["lancamento-notas-fiscais.manage"],
      is_superadmin: false,
    });

    renderPage();

    expect(
      await screen.findByText(/não tem permissão para ver os produtos sem código Delpi/i),
    ).toBeTruthy();
    expect(api.listUnmappedProducts).not.toHaveBeenCalled();
  });
});
