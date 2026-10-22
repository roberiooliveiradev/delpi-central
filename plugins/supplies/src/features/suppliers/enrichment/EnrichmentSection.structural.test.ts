import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(dir, name), "utf8");
}

describe("Enrichment feature (X4.S1) — boundaries", () => {
  it("fala somente com supplies-api via httpClient canônico", () => {
    const api = read("api.ts");
    expect(api).toContain('from "../../../api/httpClient"');
    expect(api).toContain("suppliesApiUrl");
    for (const file of readdirSync(dir).filter(
      (f) => /\.tsx?$/.test(f) && !f.endsWith(".test.ts"),
    )) {
      const text = read(file);
      expect(text).not.toMatch(/api-delpi|apiDelpi/);
      expect(text).not.toMatch(/brasilapi\.com\.br|fetch\(/);
      expect(text).not.toMatch(/Service-Authorization|s2s/i);
    }
  });

  it("usa exclusivamente os 7 endpoints do contrato S2", () => {
    const api = read("api.ts");
    expect(api).toContain("/enrichment-reviews");
    expect(api).toContain("/decisions");
    expect(api).toContain("/bulk-decisions");
    expect(api).toContain("/prepare-update");
    // nenhuma escrita ERP direta
    expect(api).not.toMatch(/httpPut|httpPatch|httpDelete/);
    expect(api).not.toContain("POST /suppliers");
  });

  it("corpos de decisão respeitam o contrato (sem campos server-owned)", () => {
    const api = read("api.ts");
    expect(api).toContain("expected_revision");
    expect(api).toContain("idempotency_key");
    expect(api).toContain("field_key");
    expect(api).toContain("field_keys");
    expect(api).not.toMatch(/actor_subject|source_id|unit_context|review_id.*body/i);
  });

  it("seção montada na ficha com âncora #enrichment", () => {
    const section = read("EnrichmentSection.tsx");
    expect(section).toContain('id="enrichment"');
    expect(section).toContain('"#enrichment"');
    const detail = readFileSync(
      join(dir, "../SupplierDetailPage.tsx"),
      "utf8",
    );
    expect(detail).toContain("EnrichmentSection");
  });

  it("kit-first: sem componentes nativos duplicando o kit", () => {
    const section = read("EnrichmentSection.tsx");
    for (const cmp of [
      "SuppliesSectionCard",
      "SuppliesActionButton",
      "SuppliesEmptyState",
      "SuppliesLoadingCard",
      "SuppliesStateBanner",
      "SuppliesModal",
    ]) {
      expect(section).toContain(cmp);
    }
    const table = read("EnrichmentComparisonTable.tsx");
    expect(table).toContain("SuppliesDataTable");
    expect(table).toContain("SuppliesStatusBadge");
    const history = read("EnrichmentHistoryTable.tsx");
    expect(history).toContain("SuppliesDataTable");
    expect(history).toContain("SuppliesCompactPagination");
  });

  it("sem permissão nova nem write gate falso", () => {
    const section = read("EnrichmentSection.tsx");
    expect(section).not.toMatch(/supplies\.enrich|permission/i);
    const content = read("content.ts");
    expect(content).toContain("Nenhum dado foi gravado no Protheus");
    expect(content).not.toMatch(/salvar no protheus/i);
  });

  it("deep link preserva ficha — seção só renderiza fora de edição", () => {
    const detail = readFileSync(
      join(dir, "../SupplierDetailPage.tsx"),
      "utf8",
    );
    expect(detail).toMatch(/\{!editing \?\s*\(\s*<EnrichmentSection/);
  });
});
