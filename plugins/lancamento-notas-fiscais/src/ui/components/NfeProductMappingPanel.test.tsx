import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NfeProductMappingPanel } from "./NfeProductMappingPanel";

afterEach(() => cleanup());

describe("NfeProductMappingPanel", () => {
  it("aguarda o fornecedor", () => {
    render(<NfeProductMappingPanel view={{ status: "supplier_required" }} />);
    expect(screen.getByTestId("nfe-mapping-waiting").textContent).toMatch(/fornecedor\/loja/i);
  });

  it("mostra carregamento e erro", () => {
    const loading = render(<NfeProductMappingPanel view={{ status: "loading" }} />);
    expect(screen.getByTestId("nfe-mapping-loading")).toBeTruthy();
    loading.unmount();
    render(<NfeProductMappingPanel view={{ status: "error", message: "XML indisponível" }} />);
    expect(screen.getByTestId("nfe-mapping-error").textContent).toBe("XML indisponível");
  });

  it("mostra relacionado, não relacionado e ambíguo sem escolher candidato", () => {
    render(
      <NfeProductMappingPanel
        view={{
          status: "ready",
          detail: {
            items: [
              {
                itemNumber: "1",
                supplierProductCode: "00001234",
                supplierProductDescription: "PARAFUSO XYZ",
                internalProductCode: "000050",
                internalProductDescription: "PARAFUSO M6",
                quantity: "10",
                unit: "PC",
                mappingStatus: "mapped",
              },
              {
                itemNumber: "2",
                supplierProductCode: "ABC999",
                supplierProductDescription: "SEM",
                internalProductCode: null,
                internalProductDescription: null,
                quantity: "1",
                unit: "UN",
                mappingStatus: "unmapped",
              },
              {
                itemNumber: "3",
                supplierProductCode: "ABC-1.2",
                supplierProductDescription: "AMB",
                internalProductCode: null,
                internalProductDescription: null,
                quantity: "2",
                unit: "PC",
                mappingStatus: "ambiguous",
              },
            ],
            summary: { items: 3, mapped: 1, unmapped: 1, ambiguous: 1 },
          },
        }}
      />,
    );
    expect(screen.getByText("00001234")).toBeTruthy();
    expect(screen.getByText("000050")).toBeTruthy();
    expect(screen.getByText("10 PC")).toBeTruthy();
    expect(screen.getByText("Relacionado")).toBeTruthy();
    expect(screen.getAllByText("Não relacionado").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Relação ambígua").length).toBeGreaterThan(0);
    expect(screen.queryByText("DELPI999")).toBeNull();
    expect(screen.getByTestId("nfe-item-summary").textContent).toMatch(/3 itens/);
    expect(screen.getByTestId("nfe-item-summary").textContent).toMatch(/1 não relacionado/);
    expect(screen.getByTestId("nfe-item-summary").textContent).toMatch(/1 ambíguo/);
  });

  it("não mostra código Delpi quando o fornecedor diverge", () => {
    render(
      <NfeProductMappingPanel
        view={{
          status: "issuer_mismatch",
          detail: {
            items: [
              {
                itemNumber: "1",
                supplierProductCode: "00001234",
                supplierProductDescription: "PARAFUSO",
                quantity: "1",
                unit: "PC",
                internalProductCode: null,
                mappingStatus: null,
              },
            ],
          },
        }}
      />,
    );
    expect(screen.getByTestId("nfe-mapping-mismatch").textContent).toMatch(/não corresponde/i);
    expect(screen.getByText("00001234")).toBeTruthy();
    expect(screen.queryByText("000050")).toBeNull();
  });
});
