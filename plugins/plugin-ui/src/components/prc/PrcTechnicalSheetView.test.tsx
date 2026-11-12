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

describe("PrcTechnicalSheetView — modo UPDATE (alterações solicitadas)", () => {
  const UPDATE_DRAFT = {
    officialProductCode: "10080025",
    description: "Terminal olhal M6 estanhado com isolação",
    unit: "PC",
    group: "02",
    productKind: "MP",
    defaultWarehouse: "01",
  };

  it("exibe apenas o campo alterado com antes/solicitado — sem duplicação nem objeto bruto", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[
          { path: "description", reason: "Padronização" },
        ]}
        baselineFields={{
          description: "Terminal olhal M6 estanhado",
        }}
      />,
    );
    expect(screen.getByText("Identificação do produto")).toBeTruthy();
    expect(screen.getByText("10080025")).toBeTruthy();
    expect(screen.getByText("Alterações solicitadas")).toBeTruthy();
    expect(screen.getByText("Antes")).toBeTruthy();
    expect(screen.getByText("Solicitado")).toBeTruthy();
    expect(
      screen.getByText("Terminal olhal M6 estanhado"),
    ).toBeTruthy();
    expect(
      screen.getByText("Terminal olhal M6 estanhado com isolação"),
    ).toBeTruthy();
    // Campo não alterado não aparece; sem card de fornecedores/documentos.
    expect(screen.queryByText("Estoque e contabilidade")).toBeNull();
    expect(screen.queryByText("Fornecedores")).toBeNull();
    expect(screen.queryByText(/object Object/)).toBeNull();
  });

  it("extrai o valor das entradas {value,present} do baseline (contrato D15)", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[
          { path: "description", reason: "" },
          { path: "unit", reason: "" },
        ]}
        baselineFields={{
          description: {
            value: "TERM. OLHAL M6 ESTANHADO",
            present: true,
            officialField: "description",
          },
          unit: { value: "UN", present: true, officialField: "unit" },
        }}
      />,
    );
    expect(screen.getByText("TERM. OLHAL M6 ESTANHADO")).toBeTruthy();
    expect(screen.getByText("UN")).toBeTruthy();
    expect(screen.queryByText(/object Object/)).toBeNull();
    expect(screen.queryByText("Não disponível")).toBeNull();
  });

  it("múltiplos campos; baseline com estrutura não reconhecida vira estado indisponível", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[
          { path: "description", reason: "" },
          { path: "unit", reason: "" },
          { path: "suppliers", reason: "" },
        ]}
        baselineFields={{
          description: { valor: "estrutura legada" },
          unit: { value: "UN", present: true },
        }}
      />,
    );
    // Descrição com baseline de formato desconhecido → estado explícito.
    expect(screen.getAllByText("Não disponível").length).toBeGreaterThan(0);
    expect(screen.queryByText(/object Object/)).toBeNull();
    // Unidade: antes correto via entry {value,present}.
    expect(screen.getByText("UN")).toBeTruthy();
    expect(screen.getByText("PC")).toBeTruthy();
    // Path suppliers não vira linha escalar.
    expect(screen.queryByText("Fornecedores")).toBeNull();
  });

  it("campo ausente no produto oficial (present:false) exibe estado correto", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[{ path: "customerReference", reason: "" }]}
        baselineFields={{
          customerReference: { value: "", present: false },
        }}
      />,
    );
    expect(
      screen.getByText("Não informado no cadastro oficial"),
    ).toBeTruthy();
  });

  it("renderiza operação de inclusão de fornecedor", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[]}
        supplierLinkChanges={[
          {
            operation: "add",
            key: { supplierCode: "000125", store: "01" },
            fields: { partNumber: "PN-NEW", catalogNumber: "CAT-1" },
            supplierName: "ABC Componentes Ltda.",
          },
        ]}
      />,
    );
    expect(screen.getByText("Adicionar fornecedor")).toBeTruthy();
    expect(screen.getByText(/000125 \/ 01 — ABC Componentes/)).toBeTruthy();
    expect(screen.getByText("PN-NEW")).toBeTruthy();
    // Sem alegação de que outros fornecedores inexistem.
    expect(screen.queryByText("Nenhum fornecedor vinculado.")).toBeNull();
  });

  it("renderiza remoção como solicitada (não efetivada)", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[]}
        supplierLinkChanges={[
          {
            operation: "remove",
            key: { supplierCode: "000987", store: "02" },
          },
        ]}
        baselineLinks={[
          {
            supplierCode: "000987",
            store: "02",
            supplierName: "Resinas do Sul SA",
            partNumber: "PN-77",
          },
        ]}
      />,
    );
    expect(screen.getByText("Remover vínculo")).toBeTruthy();
    expect(screen.getByText(/Resinas do Sul SA/)).toBeTruthy();
    expect(screen.getByText(/pendente de efetivação/)).toBeTruthy();
    expect(screen.getByText("PN-77")).toBeTruthy();
  });

  it("update de vínculo compara apenas o atributo alterado", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[]}
        supplierLinkChanges={[
          {
            operation: "update",
            key: { supplierCode: "000123", store: "01" },
            fields: { partNumber: "PN-55-B" },
          },
        ]}
        baselineLinks={[
          {
            supplierCode: "000123",
            store: "01",
            supplierName: "Fornecedor Química LTDA",
            partNumber: "PN-55-A",
            catalogNumber: "CAT-9",
          },
        ]}
      />,
    );
    expect(screen.getByText("Alterar vínculo")).toBeTruthy();
    expect(screen.getByText("PN-55-A")).toBeTruthy();
    expect(screen.getByText("PN-55-B")).toBeTruthy();
    // Catálogo não alterado → não listado.
    expect(screen.queryByText("CAT-9")).toBeNull();
  });

  it("antes indisponível quando baseline não contém o path", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[{ path: "description", reason: "" }]}
        baselineFields={{}}
      />,
    );
    expect(screen.getByText("Não disponível")).toBeTruthy();
  });

  it("mantém ids de alvo para navegação/flags nos campos alterados", () => {
    render(
      <PrcTechnicalSheetView
        requestType="update"
        draft={UPDATE_DRAFT}
        changedPaths={[{ path: "unit", reason: "" }]}
        baselineFields={{ unit: "UN" }}
      />,
    );
    expect(document.getElementById("prc-field-unit")).toBeTruthy();
  });
});
