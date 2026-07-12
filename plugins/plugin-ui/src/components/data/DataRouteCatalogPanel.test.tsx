import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
  it("agrupa, busca e dispara onSelect", () => {
    const onSelect = vi.fn();

    render(
      <DataRouteCatalogPanel
        items={ITEMS}
        onSelect={onSelect}
        categoryLabels={{ production: "Produção", products: "Produtos" }}
        categoryOrder={["production", "products"]}
      />,
    );

    expect(screen.getByRole("group", { name: "Categorias" })).toBeTruthy();
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(
      screen.getByText((_, node) =>
        Boolean(
          node?.classList.contains("delpi-ui-data-route-catalog__path") &&
            node.textContent?.replace(/\s+/g, " ").trim() === "GET /production/oee",
        ),
      ),
    ).toBeTruthy();
    expect(screen.getByText(/Indicador consolidado/)).toBeTruthy();

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "busca" } });
    expect(screen.queryByText("OEE geral")).toBeNull();
    expect(screen.getByText("Produtos — busca")).toBeTruthy();

    fireEvent.click(screen.getByText("Produtos — busca"));
    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: "search_products", label: "Produtos — busca" }),
    );
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
});
