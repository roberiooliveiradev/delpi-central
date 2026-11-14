import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import type { PrcRequestSummary } from "../api/productRegistrationApi";
import type { DataTableColumn } from "../../lmps/components/dataTableUi";
import { buildPrcCardColumns } from "./PrcRequestCard";

const here = dirname(fileURLToPath(import.meta.url));

function col(key: string): DataTableColumn<PrcRequestSummary> {
  return { key, header: key.toUpperCase(), render: (r) => r.id };
}

describe("§47 buildPrcCardColumns — catálogo único Cards ≡ Kanban", () => {
  const all = [
    "id",
    "type",
    "requester",
    "officialCode",
    "createdAt",
    "status",
    "assignedTo",
  ].map(col);

  it("identidade (id) sempre à frente, seguida dos visíveis na ordem da preferência", () => {
    const visible = [col("status"), col("type")];
    expect(buildPrcCardColumns(all, visible).map((c) => c.key)).toEqual([
      "id",
      "status",
      "type",
    ]);
  });

  it("id permanece presente mesmo oculto na tabela (identidade acessível)", () => {
    const visible = all.filter((c) => c.key !== "id");
    const out = buildPrcCardColumns(all, visible).map((c) => c.key);
    expect(out[0]).toBe("id");
    expect(out).toHaveLength(all.length);
  });

  it("campo oculto some do card — mesma configuração da tabela", () => {
    const visible = all.filter((c) => c.key !== "createdAt");
    const out = buildPrcCardColumns(all, visible).map((c) => c.key);
    expect(out).not.toContain("createdAt");
    expect(out).toContain("id");
  });

  it("reordenação da preferência é respeitada", () => {
    const visible = [col("status"), col("id"), col("type")];
    const out = buildPrcCardColumns(all, visible).map((c) => c.key);
    expect(out).toEqual(["id", "status", "type"]);
  });

  it("omitKeys remove Status no Kanban sem perder identidade", () => {
    const out = buildPrcCardColumns(all, all, {
      omitKeys: ["status"],
    }).map((c) => c.key);
    expect(out).not.toContain("status");
    expect(out[0]).toBe("id");
  });
});

describe("§47 PrcRequestCard — contrato estrutural", () => {
  const src = readFileSync(join(here, "PrcRequestCard.tsx"), "utf8");

  it("usa o card interativo canônico do kit (teclado/ariaLabel/openHint)", () => {
    expect(src).toContain("EngineeringInteractiveDataCard");
    expect(src).toContain("ariaLabel={`Solicitação ${prcShortId(row.id)}`}");
    expect(src).toContain("onActivate={() => onOpen(row)}");
    expect(src).toContain("openHint={PRC_COPY.openRequest}");
  });

  it("renderiza os campos do catálogo via column.render — sem mapeamento duplicado", () => {
    expect(src).toContain("columns.map((column)");
    expect(src).toContain("value: column.render(row)");
    expect(src).not.toContain("PRC_STATUS_LABELS[");
    expect(src).not.toContain("PRC_TYPE_LABELS[");
  });
});

describe("§47 PrcQueuePage — Cards e Kanban compartilham o card", () => {
  const page = readFileSync(
    join(here, "..", "pages", "PrcQueuePage.tsx"),
    "utf8",
  );

  it("os dois modos usam PrcRequestCard (Cards + Kanban)", () => {
    const uses = page.match(/<PrcRequestCard/g) ?? [];
    expect(uses.length).toBe(2);
    expect(page).toContain("columns={cardColumns}");
    expect(page).toContain("columns={kanbanCardColumns}");
  });

  it("menu Colunas disponível nos três modos (sem gate de layout)", () => {
    expect(page).not.toMatch(
      /layout === "table" \? \(\s*<TableColumnVisibilityMenu/,
    );
    expect(page).toContain("<TableColumnVisibilityMenu");
  });

  it("Kanban sinaliza itens da página vs. total do universo", () => {
    expect(page).toContain("formatPrcKanbanColumnCountMeta");
    expect(page).toContain("displayedOnPage");
    expect(page).toContain("totalInScope");
    expect(page).toContain("paginação server-side preservada");
  });
});
