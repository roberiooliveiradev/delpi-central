import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DataRouteCatalogPanel,
  primaryDataRouteDisplayKind,
  resolveDataRouteDisplayKinds,
  type DataRouteCatalogItem,
} from "./DataRouteCatalogPanel";

afterEach(() => {
  cleanup();
});

const ITEMS: DataRouteCatalogItem[] = [
  {
    id: "get_oee",
    label: "OEE geral",
    category: "production",
    path: "/production/oee",
    httpMethod: "GET",
    description: "Indicador consolidado de eficiência.",
    metaShape: "scalar",
    displayKinds: ["kpi"],
    params: [{ key: "branch", label: "Filial", optional: true }],
  },
  {
    id: "search_products",
    label: "Produtos — busca",
    category: "products",
    path: "/products/search",
    httpMethod: "GET",
    description: "Listagem paginada de produtos.",
    metaShape: "paged_list",
    displayKinds: ["table"],
    params: [
      { key: "q", label: "Busca", optional: false },
      { key: "limit", label: "Limite", optional: true },
    ],
  },
  {
    id: "oee_series",
    label: "OEE — série",
    category: "production",
    path: "/production/oee/series",
    httpMethod: "GET",
    metaShape: "playbook_report",
    displayKinds: ["series", "kpi"],
  },
];

describe("resolveDataRouteDisplayKinds", () => {
  it("prioriza displayKinds explícitos", () => {
    expect(resolveDataRouteDisplayKinds({ displayKinds: ["kpi", "table"] })).toEqual(["kpi", "table"]);
  });

  it("deriva de metaShape e modos permitidos", () => {
    expect(resolveDataRouteDisplayKinds({ metaShape: "scalar" })).toEqual(["kpi"]);
    expect(
      resolveDataRouteDisplayKinds({
        metaShape: "paged_list",
        allowedDisplayModes: ["table", "line_chart"],
      }),
    ).toEqual(expect.arrayContaining(["table", "series"]));
  });

  it("escolhe primaryKind com série primeiro", () => {
    expect(primaryDataRouteDisplayKind(["kpi", "series"])).toBe("series");
    expect(primaryDataRouteDisplayKind(["kpi", "table"])).toBe("kpi");
  });
});

describe("DataRouteCatalogPanel", () => {
  it("lista amigável sem path no card; detalhe exige confirmar", () => {
    const onSelect = vi.fn();

    render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={onSelect}
        density="comfortable"
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    expect(screen.getByRole("group", { name: "Categorias" })).toBeTruthy();
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(screen.queryByText("GET /production/oee")).toBeNull();
    expect(screen.getByText("1 filtro")).toBeTruthy();
    expect(screen.queryByRole("complementary")).toBeNull();

    fireEvent.click(screen.getByText("OEE geral"));
    const detail = screen.getByRole("complementary", { name: /Detalhe: OEE geral/ });
    expect(detail).toBeTruthy();
    expect(detail.textContent).toMatch(/Para que serve/);
    expect(detail.textContent).toMatch(/Indicador consolidado/);
    expect(detail.textContent).toMatch(/Filial/);
    expect(detail.textContent).toMatch(/Exemplo de uso/);
    expect(screen.getByLabelText("Prévia KPI")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Usar esta fonte" }));
    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: "get_oee", label: "OEE geral" }));
  });

  it("fecha o detalhe pelo botão e mostra exemplo tipado por forma", () => {
    render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={vi.fn()}
        density="comfortable"
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    fireEvent.click(screen.getByText("Produtos — busca"));
    expect(screen.getByRole("complementary", { name: /Detalhe: Produtos/ })).toBeTruthy();
    expect(screen.getByText("Exemplo de uso")).toBeTruthy();
    expect(screen.getByText("Código")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Fechar detalhe" }));
    expect(screen.queryByRole("complementary")).toBeNull();
  });

  it("testar rota usa callback e substitui o exemplo pelo resultado", async () => {
    const onTestRoute = vi.fn().mockResolvedValue({
      kind: "kpi",
      source: "live",
      kpi: { label: "OEE live", value: "91,2%" },
    });

    render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={vi.fn()}
        onTestRoute={onTestRoute}
        density="comfortable"
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    fireEvent.click(screen.getByText("OEE geral"));
    fireEvent.click(screen.getByRole("button", { name: "Testar rota" }));

    await waitFor(() => expect(onTestRoute).toHaveBeenCalled());
    expect(screen.getByText("Resultado do teste")).toBeTruthy();
    expect(screen.getByText("91,2%")).toBeTruthy();
    expect(screen.queryByText("Exemplo de uso")).toBeNull();
  });
  it("filtra por categoria e forma (KPI)", () => {
    const { container } = render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={vi.fn()}
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    const productionChip = Array.from(container.querySelectorAll(".delpi-ui-data-route-catalog__chip")).find((el) =>
      (el.textContent ?? "").startsWith("Produção"),
    );
    expect(productionChip).toBeTruthy();
    fireEvent.click(productionChip!);
    expect(screen.getByText(/2 fontes · Produção/)).toBeTruthy();
    expect(screen.queryByText("Produtos — busca")).toBeNull();
    expect(screen.getByText("OEE geral")).toBeTruthy();

    const kpiChip = Array.from(container.querySelectorAll(".delpi-ui-data-route-catalog__chip--kind")).find(
      (el) => el.textContent === "KPI",
    );
    expect(kpiChip).toBeTruthy();
    fireEvent.click(kpiChip!);
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(screen.getByText("OEE — série")).toBeTruthy();
    expect(screen.queryByText("Produtos — busca")).toBeNull();
  });

  it("busca por label e mostra path só em avançado", () => {
    render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={vi.fn()}
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "busca" } });
    expect(screen.queryByText("OEE geral")).toBeNull();
    expect(screen.getByText("Produtos — busca")).toBeTruthy();

    fireEvent.click(screen.getByText("Produtos — busca"));
    fireEvent.click(screen.getByText("Avançado (API)"));
    expect(screen.getByText("GET /products/search")).toBeTruthy();
    expect(screen.getByText("2 filtros · 1 obrigatório")).toBeTruthy();
  });
});
