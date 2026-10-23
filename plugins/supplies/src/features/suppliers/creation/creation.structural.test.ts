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
