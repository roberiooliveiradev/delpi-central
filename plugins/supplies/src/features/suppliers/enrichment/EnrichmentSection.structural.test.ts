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

  it("RETRY = SAME OPERATION — retry executa a operação capturada", () => {
    const section = read("EnrichmentSection.tsx");
    // retry chama runOperation(failedOp) — nunca reconstrói de estado mutável
    expect(section).toContain("runOperation(failedOp)");
    // captura ocorre na intenção, com chave nova por operação
    expect(section).toMatch(/captureSingleDecision\(/);
    expect(section).toMatch(/captureBulkDecision\(/);
    // newIdempotencyKey só pode aparecer nos pontos de captura (nova intenção)
    const keySites = section.match(/newIdempotencyKey\(\)/g) ?? [];
    expect(keySites).toHaveLength(2); // single + bulk; retry nunca gera chave
  });

  it("operação pendente é descartada fora do contexto original", () => {
    const section = read("EnrichmentSection.tsx");
    // abrir outra revisão, criar consulta nova ou trocar fornecedor limpa failedOp
    expect(section.match(/setFailedOp\(null\)/g)?.length).toBeGreaterThanOrEqual(4);
  });

  it("conflitos 409 não disparam retry automático", () => {
    const ops = read("decisionOperations.ts");
    expect(ops).toContain("isRecoverableForRetry");
    expect(ops).toMatch(/status >= 500 \|\| err\.status === 429/);
  });

  it("S9.R1 — fonte/data usam os formatadores compartilhados", () => {
    const section = read("EnrichmentSection.tsx");
    const history = read("EnrichmentHistoryTable.tsx");
    for (const text of [section, history]) {
      expect(text).toContain("../externalSourceFormat");
      expect(text).toContain("providerDisplayName");
      expect(text).toContain("formatRetrievedAt");
    }
    // sem timestamp bruto como texto principal nem fuso do relógio local
    // padrão bruto pode aparecer apenas dentro de title= (proveniência),
    // nunca como texto principal — exatamente 1 ocorrência
    const rawMeta = section.match(/active\.review\.source_id\} · /g) ?? [];
    expect(rawMeta).toHaveLength(1);
    expect(history).not.toContain("toLocaleString");
    // proveniência técnica preservada via title
    expect(section).toMatch(/title=\{`?\$?\{?active\.review\.source_id/);
    expect(history).toContain("title={r.source_id}");
  });

  it("S9.R1 — formatadores canônicos moram no bounded context suppliers", () => {
    const shared = readFileSync(
      join(dir, "../externalSourceFormat.ts"),
      "utf8",
    );
    expect(shared).toContain('PORTAL_TIME_ZONE = "America/Sao_Paulo"');
    expect(shared).toContain("brasilapi-cnpj-v1");
    const creationContent = readFileSync(
      join(dir, "../creation/content.ts"),
      "utf8",
    );
    // re-export — única fonte, sem duplicar o formatador
    expect(creationContent).toContain('from "../externalSourceFormat"');
    expect(creationContent).not.toContain("formatToParts");
  });

  it("prepare-update não carrega idempotência fictícia", () => {
    const ops = read("decisionOperations.ts");
    // variante "prepare" da operação carrega apenas expectedRevision
    expect(ops).toMatch(
      /kind: "prepare";\s*\n\s*code: string;\s*\n\s*store: string;\s*\n\s*reviewId: string;\s*\n\s*expectedRevision: number;/,
    );
    const api = read("api.ts");
    // corpo real do prepare é apenas expected_revision
    expect(api).toMatch(/prepare-update[\s\S]*expected_revision: expectedRevision/);
  });
});
