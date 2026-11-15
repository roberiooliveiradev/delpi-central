import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { PrcProductSummary } from "../api/productRegistrationApi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { buildPrcProductCardColumns } from "./PrcProductCard";
import {
  PRC_PRODUCT_COLUMN_CATALOG,
  PRC_PRODUCT_FIELD_KEYS,
  prcProductCardFieldTone,
} from "../prcProductsFieldCatalog";

const here = dirname(fileURLToPath(import.meta.url));

function col(key: string): DataTableColumn<PrcProductSummary> {
  return { key, header: key.toUpperCase(), render: (r) => r.officialCode };
}

const KEYS = [...PRC_PRODUCT_FIELD_KEYS];

describe("G3 buildPrcProductCardColumns — catálogo único Cards ≡ Tabela", () => {
  const all = KEYS.map(col);

  it("identidade (officialCode) sempre à frente, seguida dos visíveis na ordem da preferência", () => {
    const visible = [col("openFlagCount"), col("description")];
    expect(
      buildPrcProductCardColumns(all, visible).map((c) => c.key),
    ).toEqual(["officialCode", "openFlagCount", "description"]);
  });

  it("officialCode permanece presente mesmo oculto na tabela", () => {
    const visible = all.filter((c) => c.key !== "officialCode");
    const out = buildPrcProductCardColumns(all, visible).map(
      (c) => c.key,
    );
    expect(out[0]).toBe("officialCode");
    expect(out).toHaveLength(all.length);
  });

  it("campo oculto some do card — mesma configuração da tabela", () => {
    const visible = all.filter((c) => c.key !== "lastEvolution");
    const out = buildPrcProductCardColumns(all, visible).map(
      (c) => c.key,
    );
    expect(out).not.toContain("lastEvolution");
    expect(out).toContain("officialCode");
  });
});

describe("G3 PrcProductCard — contrato estrutural", () => {
  const src = readFileSync(join(here, "PrcProductCard.tsx"), "utf8");

  it("usa o card interativo canônico do kit (teclado/ariaLabel/openHint)", () => {
    expect(src).toContain("EngineeringInteractiveDataCard");
    expect(src).toContain("ariaLabel={`Produto ${row.officialCode}`}");
    expect(src).toContain("onActivate={() => onOpen(row)}");
    expect(src).toContain("PRC_PRODUCTS_COPY.openProduct");
    expect(src).not.toContain("`${#");
  });

  it("renderiza os campos do catálogo via column.render — sem mapeamento duplicado", () => {
    expect(src).toContain("columns.map((column)");
    expect(src).toContain("value: column.render(row)");
  });

  it("catálogo tem as 5 colunas e officialCode é tom de título", () => {
    expect(PRC_PRODUCT_COLUMN_CATALOG).toHaveLength(5);
    expect(prcProductCardFieldTone("officialCode")).toBe("title");
    expect(prcProductCardFieldTone("openFlagCount")).toBe("value");
    expect(prcProductCardFieldTone("lastEvolution")).toBe("meta");
  });
});

describe("G1–G3 PrcProductsPage — paridade com a fila", () => {
  const page = readFileSync(
    join(here, "..", "pages", "PrcProductsPage.tsx"),
    "utf8",
  );

  it("menu Colunas + toggle Tabela/Cards (sem Kanban) e sem gate de layout", () => {
    expect(page).toContain("<TableColumnVisibilityMenu");
    expect(page).toContain("<EngineeringSegmentToggle");
    expect(page).toContain('{ value: "table", label: "Tabela" }');
    expect(page).toContain('{ value: "cards", label: "Cards" }');
    expect(page).not.toContain("Kanban");
    expect(page).not.toMatch(
      /layout === "table" \? \(\s*<TableColumnVisibilityMenu/,
    );
  });

  it("preferências próprias — separadas das de Solicitações", () => {
    expect(page).toContain("engineering:prc:products:columns");
    expect(page).toContain("engineering:prc:products:layout");
    expect(page).not.toContain("engineering:prc:requests:columns");
    expect(page).not.toContain("engineering:prc:requests:layout");
  });

  it("identidade preservada como fallback de visibilidade", () => {
    expect(page).toContain('emptyFallbackKeys: ["officialCode"]');
  });

  it("cinco colunas ordenáveis — sortDir trafega para a API", () => {
    expect(page.match(/sortable: true/g)?.length).toBe(5);
    expect(page).toContain("sortDir: state.sortBy ? state.sortDir");
    expect(page).toContain('{ sort: "version", dir: "desc" }');
    expect(page).toContain('{ sort: "openFlags", dir: "desc" }');
  });
});
