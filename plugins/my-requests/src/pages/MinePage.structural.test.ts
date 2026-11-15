/** PRC-REF-023-UX-PARITY-FIX-01 — regressão estrutural da listagem
 * unificada: casos PRC NÃO podem voltar a ser parágrafos soltos em um
 * card separado; a tabela única (DataTable) deve atender as duas fontes
 * oficiais com merge honesto por data. */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(resolve(dir, "MinePage.tsx"), "utf-8");
const domain = readFileSync(
  resolve(dir, "../domain/requestListPresentation.ts"),
  "utf-8",
);

describe("MinePage — tabela unificada requests-api + PRC", () => {
  it("renderiza UMA DataTable para as duas origens", () => {
    expect(src.match(/<DataTable[\s>]/g)).toHaveLength(1);
  });

  it("não renderiza casos PRC como parágrafos nem card separado", () => {
    expect(src).not.toContain("prcItems.map");
    expect(src).not.toMatch(/prcItems\.map\([^)]*<p>/);
    expect(src).not.toContain("Cadastro de produtos e matérias-primas");
    /* um único card-section (abertura + fechamento) — sem card PRC extra */
    expect(src.match(/<MyRequestsSectionCard/g)!.length).toBe(1);
  });

  it("usa o view model unificado (UnifiedRequestRow) com fonte e destino", () => {
    expect(domain).toContain("UnifiedRequestRow");
    expect(domain).toContain('"requests-api"');
    expect(domain).toContain('"engineering-prc"');
    expect(domain).toContain("destination");
    expect(domain).toContain("fullIdentifier");
  });

  it("não inventa número sequencial para o PRC — exibe UUID legível", () => {
    expect(domain).toContain("PRC-${row.id.slice(0, 8).toUpperCase()}");
    expect(domain).not.toMatch(/request_number\s*[:=]/);
  });

  it("faz merge honesto por data com janela das duas APIs paginadas", () => {
    expect(domain).toContain("mergeUnifiedRows");
    expect(src).toContain("MERGE_WINDOW_MAX");
    expect(src).toContain("filters.page * REQUEST_LIST_PAGE_SIZE");
    /* Ambas as chamadas usam page=1 + pageSize=janela — nunca concatena
     * páginas parciais declarando total falso. */
    expect(src).toContain("page: 1,");
    expect(src).toContain("listMyPrcRequests");
  });

  it("propaga filtros para as duas fontes e trata typeCode/filial PRC", () => {
    expect(src).toContain("search: filters.q");
    expect(src).toContain("status: filters.status");
    /* ISOLATION-01 — gate canônico único decide a chamada PRC. */
    expect(src).toContain("shouldIncludePrcInList");
  });

  it("distingue erro parcial de requests-api e de Engineering API", () => {
    expect(src).toContain("setError(");
    expect(src).toContain("setPrcError(");
    expect(src).toContain("Promise.allSettled");
    /* ISOLATION-01 — falhas das integrações não vazam internals do
     * backend para a UI (mensagem contextual estática). */
    expect(src).toContain("prcListErrorMessage()");
    expect(src).not.toContain("prcRes.reason");
    expect(src).not.toContain("reqRes.reason");
  });

  it("cada linha PRC navega para /prc/{id} oficial", () => {
    expect(src).toContain("myRequestsPrcPath");
    expect(src).toContain('row.source === "engineering-prc"');
  });
});
