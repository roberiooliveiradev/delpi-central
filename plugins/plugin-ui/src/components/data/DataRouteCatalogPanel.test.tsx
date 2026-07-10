import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DataRouteCatalogPanel, type DataRouteCatalogItem } from "./DataRouteCatalogPanel";

const ITEMS: DataRouteCatalogItem[] = [
  {
    id: "get_oee",
    label: "OEE geral",
    category: "production",
    path: "/production/oee",
    httpMethod: "GET",
    description: "Indicador consolidado de eficiência.",
  },
  {
    id: "search_products",
    label: "Produtos — busca",
    category: "products",
    path: "/products/search",
    httpMethod: "GET",
  },
];

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

    expect(screen.getByText("Produção")).toBeTruthy();
    expect(screen.getByText("OEE geral")).toBeTruthy();
    expect(screen.getByText(/GET \/production\/oee/)).toBeTruthy();

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "busca" } });
    expect(screen.queryByText("OEE geral")).toBeNull();
    expect(screen.getByText("Produtos — busca")).toBeTruthy();

    fireEvent.click(screen.getByText("Produtos — busca"));
    expect(onSelect).toHaveBeenCalledWith(ITEMS[1]);
  });
});
