import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(dir, name), "utf8");
}

describe("SupplierIntegrationStatusCard (X4.REST-STATUS.S1) — boundaries", () => {
  it("fala somente com supplies-api via httpClient canônico", () => {
    const api = read("api.ts");
    expect(api).toContain('from "../../api/httpClient"');
    expect(api).toContain('"/suppliers/integration-status"');
    const card = read("SupplierIntegrationStatusCard.tsx");
    for (const text of [api, card]) {
      expect(text).not.toMatch(/api-delpi|apiDelpi/);
      expect(text).not.toMatch(/Service-Authorization|s2s/i);
      expect(text).not.toMatch(/192\.168|8061|8701|restall/i);
    }
  });

  it("diagnóstico é estritamente read-only — sem escrita ERP", () => {
    const api = read("api.ts");
    const statusFn = api.slice(api.indexOf("getSuppliersIntegrationStatus"));
    expect(statusFn).toContain("httpGet");
    expect(statusFn).not.toMatch(/httpPost|httpPut|httpDelete|httpPatch/);
  });

  it("card compartilhado montado nas duas páginas sob capabilities.manage", () => {
    for (const page of ["SuppliersPage.tsx", "SupplierDetailPage.tsx"]) {
      const text = read(page);
      expect(text).toContain("SupplierIntegrationStatusCard");
      expect(text).toContain("session.capabilities.manage");
      expect(text).toContain("useSuppliesSession");
    }
  });

  it("refresh manual sem polling nem requisições concorrentes", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).not.toMatch(/setInterval|setTimeout/);
    expect(card).toContain("AbortController");
    expect(card).toContain("requestRef");
    expect(card).toMatch(/if \(checking\) return/);
    expect(card).toContain("disabled={checking}");
  });

  it("POST/PUT habilitado nunca é apresentado como gravação comprovada", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    const content = read("content.ts");
    expect(card).toContain("statusStateNotTested");
    expect(card).toContain("statusWriteNotProvenNote");
    expect(content).not.toMatch(/gravação comprovada|POST validado|PUT validado/i);
    expect(card).not.toMatch(/post_validated|put_validated|write_proven/i);
  });

  it("estados confiáveis com timestamp e acessibilidade", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain("aria-live");
    expect(card).toContain("aria-expanded");
    expect(card).toContain('role="alert"');
    expect(card).toContain("formatCheckedAt");
    expect(card).toContain("overallBadge");
    expect(card).toContain("authentication_http_status");
  });

  it("diferencia dependência upstream de indisponibilidade geral", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain('"upstream_pending"');
    expect(card).toContain('"ready_for_attempt"');
    expect(card).toContain('"unavailable"');
    // nunca exibe "pronta" quando overall não for ready_for_attempt
    expect(card).not.toMatch(/overall.*===.*"ok"/);
  });

  it("nota de independência SQL preservada na expansão", () => {
    const card = read("SupplierIntegrationStatusCard.tsx");
    expect(card).toContain("statusSqlIndependentNote");
  });
});
