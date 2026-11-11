/** PRC-REF-023-UI-FIX-07 — regressão da ficha técnica de leitura
 * compartilhada (Engenharia + Minhas Solicitações). Prova paridade de
 * campos/fornecedores, zeros à esquerda, baseline UPDATE e os pontos
 * de extensão por perfil — sem HTTP/AuthZ no componente. */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { PrcTechnicalSheetView } from "./PrcTechnicalSheetView";

afterEach(cleanup);

const CREATE_DRAFT = {
  officialProductCode: "CANDIDATO",
  description: "Resina epóxi bicomponente",
  group: "01",
  productKind: "MP",
  unit: "KG",
  defaultWarehouse: "01",
  accountingAccount: "11301",
  thirdPartyProduct: "1",
  customerReference: "",
  suppliers: [
    {
      supplierCode: "000123",
      store: "01",
      supplierName: "Fornecedor Química LTDA",
      supplierShortName: "FQ LTDA",
      partNumber: "PN-55-A",
      catalogNumber: "CAT-9",
    },
    {
      supplierCode: "000987",
      store: "02",
      supplierName: "Resinas do Sul SA",
      partNumber: "PN-77",
    },
  ],
};

describe("PrcTechnicalSheetView — ficha CREATE", () => {
  it("renderiza grupos, campos técnicos e enums traduzidos", () => {
    render(<PrcTechnicalSheetView draft={CREATE_DRAFT} />);

    expect(
      screen.getByText("Identificação e classificação"),
    ).toBeTruthy();
    expect(screen.getByText("Estoque e contabilidade")).toBeTruthy();
    expect(screen.getByText("Resina epóxi bicomponente")).toBeTruthy();
    // Enum labels: tipo e produto de terceiros.
    expect(screen.getByText("Matéria-prima")).toBeTruthy();
    expect(screen.getByText("Não")).toBeTruthy();
    expect(screen.getByText("KG")).toBeTruthy();
    expect(screen.getByText("11301")).toBeTruthy();
  });

  it("preserva zeros à esquerda e exibe nome fantasia quando há dado", () => {
    render(<PrcTechnicalSheetView draft={CREATE_DRAFT} />);

    expect(screen.getByText("000123")).toBeTruthy();
    expect(screen.getByText("000987")).toBeTruthy();
    expect(screen.getByText("Nome fantasia")).toBeTruthy();
    expect(screen.getByText("FQ LTDA")).toBeTruthy();
    expect(screen.getByText("PN-55-A")).toBeTruthy();
    expect(screen.getByText("CAT-9")).toBeTruthy();
  });

  it("omite coluna de nome fantasia quando nenhum vínculo informa", () => {
    const draft = {
      suppliers: [
        {
          supplierCode: "000111",
          store: "01",
          supplierName: "Fornecedor A",
          partNumber: "PN-1",
        },
      ],
    };
    render(<PrcTechnicalSheetView draft={draft} />);
    expect(screen.queryByText("Nome fantasia")).toBeNull();
    expect(screen.getByText("000111")).toBeTruthy();
  });

  it("mostra estado vazio de fornecedores sem quebrar a ficha", () => {
    render(<PrcTechnicalSheetView draft={{ description: "Item" }} />);
    expect(screen.getByText("Nenhum fornecedor vinculado.")).toBeTruthy();
  });

  it("tolera draft nulo (estado parcial/erro do contrato)", () => {
    render(<PrcTechnicalSheetView draft={null} />);
    expect(screen.getByText("Nenhum fornecedor vinculado.")).toBeTruthy();
  });
});

describe("PrcTechnicalSheetView — UPDATE (baseline + justificativas)", () => {
  it("exibe nota de alteração com justificativa e valor anterior", () => {
    render(
      <PrcTechnicalSheetView
        draft={{ description: "Nova descrição", group: "02" }}
        changedPaths={[
          { path: "description", reason: "Adequação ao catálogo" },
        ]}
        baselineFields={{ description: "Descrição antiga" }}
      />,
    );

    const note = screen.getByText(/alterado:/);
    expect(note.textContent).toContain("Adequação ao catálogo");
    expect(note.textContent).toContain("antes: Descrição antiga");
  });

  it("marca alteração de fornecedores no card de vínculos", () => {
    render(
      <PrcTechnicalSheetView
        draft={CREATE_DRAFT}
        changedPaths={[
          { path: "suppliers", reason: "Novo PN do fornecedor" },
        ]}
      />,
    );
    const note = screen.getByText(/alterado:/);
    expect(note.textContent).toContain("Novo PN do fornecedor");
  });
});

describe("PrcTechnicalSheetView — pontos de extensão por perfil", () => {
  it("invoca fieldAdornment por campo (flags de atendimento)", () => {
    const adornment = vi.fn().mockReturnValue(null);
    render(
      <PrcTechnicalSheetView
        draft={CREATE_DRAFT}
        fieldAdornment={adornment}
      />,
    );
    const calledPaths = adornment.mock.calls.map((c) => c[0]);
    expect(calledPaths).toContain("description");
    expect(calledPaths).toContain("defaultWarehouse");
    // Código oficial nunca recebe flag de acompanhamento.
    expect(calledPaths).not.toContain("officialProductCode");
  });

  it("invoca supplierAdornment para partNumber e catalogNumber", () => {
    const adornment = vi.fn().mockReturnValue(null);
    render(
      <PrcTechnicalSheetView
        draft={CREATE_DRAFT}
        supplierAdornment={adornment}
      />,
    );
    const attrs = adornment.mock.calls.map((c) => c[1]);
    expect(attrs).toContain("partNumber");
    expect(attrs).toContain("catalogNumber");
    // Um por vínculo e por atributo.
    expect(adornment).toHaveBeenCalledTimes(4);
  });

  it("renderiza ação de cabeçalho injetada pelo host", () => {
    render(
      <PrcTechnicalSheetView
        draft={CREATE_DRAFT}
        suppliersHeaderActions={<button>Editar ficha</button>}
      />,
    );
    expect(screen.getByText("Editar ficha")).toBeTruthy();
  });
});
