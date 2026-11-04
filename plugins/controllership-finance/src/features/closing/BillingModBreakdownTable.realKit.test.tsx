/**
 * R09 — prova de busca e paginação no `DataTableSection` REAL do kit
 * (sem `pluginUiMock`): `getSearchText` indexa produto/descrição/filial
 * e a paginação cliente não omite registros do conjunto retornado.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

// `?raw` de assets fora do root não resolve no Vitest (limitação
// documentada em vitest.config.ts); o logo é cosmético para estes
// testes — mock do módulo de marca, mantendo o kit real no restante.
vi.mock("../../../../plugin-ui/src/brand/delpiLogoMark", () => ({
  DELPI_LOGO_MARK_SVG: "",
  DelpiLogoMark: () => null,
}));

import { DataTableSection } from "../../app/cfDataTableUi";
import type { BillingModAnchor } from "../../api/billingModBreakdownApi";

const columns = [
  {
    key: "product",
    header: "Produto",
    render: (row: BillingModAnchor) => (
      <div>
        <div>{row.product}</div>
        <div className="cf-cell-muted">
          {row.productDescription}
        </div>
      </div>
    ),
  },
  {
    key: "branch",
    header: "Filial",
    render: (row: BillingModAnchor) => row.branch ?? "—",
  },
];

const getSearchText = (row: BillingModAnchor) =>
  `${row.product} ${row.productDescription ?? ""} ${row.branch ?? ""}`;

const keyOf = (a: BillingModAnchor) => `${a.branch ?? "—"}::${a.product}`;

afterEach(cleanup);

const tbodyOf = (container: HTMLElement) =>
  within(container.querySelector("tbody")!);

function fixture(n: number): BillingModAnchor[] {
  return Array.from({ length: n }, (_, i) => ({
    branch: i % 2 === 0 ? "01" : "02",
    product: `P${String(i + 1).padStart(4, "0")}`,
    productDescription:
      i % 3 === 0 ? `Transformador óleo ${i + 1}` : `Relé ${i + 1}`,
    billedQty: i,
    modLines: [],
  }));
}

describe("R09 — busca e paginação com DataTableSection real", () => {
  it("busca por código filtra as linhas exibidas", async () => {
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={fixture(60)}
        rowKey={keyOf}
        getSearchText={getSearchText}
      />,
    );
    const input = container.querySelector("input[type=\"search\"]")!;
    fireEvent.change(input, { target: { value: "P0007" } });
    expect((await tbodyOf(container).findAllByText("P0007")).length).toBeGreaterThan(0);
    expect(tbodyOf(container).queryAllByText("P0008")).toHaveLength(0);
  });

  it("busca por parte da descrição acentuada filtra corretamente", async () => {
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={fixture(30)}
        rowKey={keyOf}
        getSearchText={getSearchText}
      />,
    );
    fireEvent.input(container.querySelector("input[type=\"search\"]")!, {
      target: { value: "Transformador" },
    });
    expect((await tbodyOf(container).findAllByText("P0001")).length).toBeGreaterThan(0);
    expect(tbodyOf(container).queryAllByText("P0002")).toHaveLength(0);
  });

  it("busca por filial distingue o mesmo produto em 01 e 02", async () => {
    const rows = [
      { ...fixture(1)[0], branch: "01", product: "PX", productDescription: "A" },
      { ...fixture(1)[0], branch: "02", product: "PX", productDescription: "A" },
    ];
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={rows}
        rowKey={keyOf}
        getSearchText={getSearchText}
      />,
    );
    fireEvent.input(container.querySelector("input[type=\"search\"]")!, {
      target: { value: "A 02" },
    });
    expect((await tbodyOf(container).findAllByText("02")).length).toBeGreaterThan(0);
    expect(tbodyOf(container).queryAllByText("01")).toHaveLength(0);
  });

  it("busca sem resultado mostra mensagem vazia; limpar restaura", async () => {
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={fixture(10)}
        rowKey={keyOf}
        getSearchText={getSearchText}
        emptyMessage="Nenhuma âncora encontrada."
      />,
    );
    const input = container.querySelector("input[type=\"search\"]")!;
    fireEvent.change(input, { target: { value: "INEXISTENTE" } });
    expect((await screen.findAllByText("Nenhuma âncora encontrada.")).length).toBeGreaterThan(0);
    fireEvent.change(input, { target: { value: "" } });
    expect((await tbodyOf(container).findAllByText("P0001")).length).toBeGreaterThan(0);
  });

  it("paginação cliente cobre o universo: última página de 521", async () => {
    const rows = fixture(521);
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={rows}
        rowKey={keyOf}
        getSearchText={getSearchText}
      />,
    );
    // navega até a última página via controle do kit
    const next = within(container).getAllByRole("button", { name: /próxim/i })[0];
    // página 1: P0001 visível; avança até a última página
    for (let i = 0; i < 11; i += 1) {
      if (!next.hasAttribute("disabled")) fireEvent.click(next);
    }
    expect((await tbodyOf(container).findAllByText("P0521")).length).toBeGreaterThan(0);
    expect(tbodyOf(container).queryAllByText("P0001")).toHaveLength(0);
  });

  it("busca reduz resultado e paginação acompanha", async () => {
    const { container } = render(
      <DataTableSection<BillingModAnchor>
        title="Produtos"
        columns={columns}
        rows={fixture(120)}
        rowKey={keyOf}
        getSearchText={getSearchText}
      />,
    );
    fireEvent.input(container.querySelector("input[type=\"search\"]")!, {
      target: { value: "Relé" },
    });
    // Relé existe nos índices ímpares (i%3!=0): ~80 registros
    expect((await tbodyOf(container).findAllByText("P0002")).length).toBeGreaterThan(0);
    expect(tbodyOf(container).queryAllByText("P0001")).toHaveLength(0);
  });
});
