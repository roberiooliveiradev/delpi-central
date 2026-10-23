import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

function read(name: string): string {
  return readFileSync(join(dir, name), "utf8");
}

describe("Creation preview (X4.UX-R1.S2) — boundaries", () => {
  it("fala somente com supplies-api via httpClient canônico", () => {
    const api = read("api.ts");
    expect(api).toContain('from "../../../api/httpClient"');
    expect(api).toContain("suppliesApiUrl");
    expect(api).toContain("/suppliers/creation-preview");
    for (const file of readdirSync(dir).filter(
      (f) => /\.tsx?$/.test(f) && !f.endsWith(".test.ts"),
    )) {
      const text = read(file);
      expect(text).not.toMatch(/api-delpi|apiDelpi/);
      expect(text).not.toMatch(/brasilapi\.com\.br|fetch\(/);
      expect(text).not.toMatch(/Service-Authorization|s2s/i);
    }
  });

  it("a prévia nunca persiste: só POST creation-preview, nenhum write", () => {
    const api = read("api.ts");
    expect(api).not.toMatch(/httpPut|httpPatch|httpDelete/);
    expect(api).not.toMatch(/\/suppliers['"`]/);
  });

  it("fluxo integrado na página de criação existente — sem segunda rota", () => {
    const page = readFileSync(
      join(dir, "../SupplierCreatePage.tsx"),
      "utf8",
    );
    expect(page).toContain("CreationAssistedFlow");
    expect(page).toContain("applyDraftPatchToEntries");
    // mesma revisão final — o flow não tem submit próprio
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).not.toMatch(/createSupplier\(|confirmSubmit|reviewing/);
  });

  it("busca nominal declarada como indisponível — sem pesquisa falsa", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("modeNameUnavailableTitle");
    expect(flow).not.toMatch(/external-search|companies\/search/);
  });

  it("respostas obsoletas são protegidas por abort + sequência", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("AbortController");
    expect(flow).toContain("requestSeq");
  });

  it("identidade nunca é sobrescrita silenciosamente (S2.R1 Defect A)", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("identityChangeCheck");
    expect(flow).toContain("confirmIdentity");
    expect(flow).toContain("window.confirm");
    // nenhum patch direto de tax_id fora da confirmação de identidade
    expect(flow).not.toMatch(
      /onApplyPatch\(\{\s*tax_id:\s*cnpjDigits/,
    );
  });

  it("digitação de novo CNPJ invalida preview anterior (S2.R1 Defect B)", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("searchTaxIdChanged");
    expect(flow).toContain("handleCnpjChange");
    expect(flow).toContain("activeTaxId");
    expect(flow).toContain("isIdentityCoherent");
    const panel = read("CreationSuggestionsPanel.tsx");
    expect(panel).toContain("identityBlocked");
    const machine = read("stateMachine.ts");
    expect(machine).toContain("identityChangeCheck");
    expect(machine).toContain("isIdentityCoherent");
    expect(machine).toContain("searchTaxIdChanged");
  });

  it("coerência cobre tax_id E person_type (S2.R2)", () => {
    const machine = read("stateMachine.ts");
    const sig = machine.match(
      /export function isIdentityCoherent\([\s\S]*?\n\}/,
    );
    expect(sig?.[0]).toContain("consultedPersonType");
    expect(sig?.[0]).toContain("person_type");
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("activePersonType");
    // guarda dupla: painel bloqueia visualmente E handlers revalidam
    expect(flow.match(/isIdentityCoherent/g)?.length).toBeGreaterThanOrEqual(
      3,
    );
  });
});

describe("Cadastros existentes por CNPJ (X4.UX-R1.S8)", () => {
  it("paginação reutiliza o componente canônico e o endpoint BFF", () => {
    const panel = read("CreationExistingSuppliersPanel.tsx");
    expect(panel).toContain("SuppliesCompactPagination");
    expect(panel).toContain("listExistingSuppliers");
    const api = read("api.ts");
    expect(api).toContain("/suppliers/existing-suppliers");
    expect(api).toContain("httpGet");
    expect(api).not.toMatch(/httpPut|httpPatch|httpDelete/);
  });

  it("conferência abre E14 em nova aba — rascunho preservado", () => {
    const panel = read("CreationExistingSuppliersPanel.tsx");
    expect(panel).toContain("buildSupplierDetailPath");
    expect(panel).toContain('target="_blank"');
    expect(panel).toContain('rel="noopener noreferrer"');
    // nunca navega a própria aba para fora do rascunho
    expect(panel).not.toContain("navigatePluginPath");
    // nenhuma persistência improvisada no browser
    for (const file of readdirSync(dir).filter(
      (f) => /\.tsx?$/.test(f) && !f.endsWith(".test.ts"),
    )) {
      const text = read(file);
      expect(text).not.toMatch(/localStorage|sessionStorage|indexedDB/);
    }
  });

  it("aviso de duplicidade é informativo e não bloqueia o formulário", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("CreationExistingSuppliersPanel");
    expect(flow).toContain("duplicatePossibleFooter");
    const content = read("content.ts");
    expect(content).toContain("Você pode continuar o preenchimento");
    // o banner POSSIBLE_MATCH não é mais de erro
    const match = flow.match(/POSSIBLE_MATCH[\s\S]*?<\/SuppliesStateBanner>/);
    expect(match?.[0]).not.toContain('variant="error"');
  });

  it("total real vem do contrato — nunca inventado", () => {
    const flow = read("CreationAssistedFlow.tsx");
    expect(flow).toContain("duplicate_check.total");
    const api = read("api.ts");
    expect(api).toContain("page_size");
  });
});
