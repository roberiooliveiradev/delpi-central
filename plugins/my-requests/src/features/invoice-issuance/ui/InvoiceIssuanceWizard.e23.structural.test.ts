import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const wizardPath = join(__dirname, "InvoiceIssuanceWizard.tsx");

describe("InvoiceIssuanceWizard E23 pickers", () => {
  const source = readFileSync(wizardPath, "utf8");

  it("usa EntityDirectoryPicker nas 3 buscas sem botão Buscar", () => {
    expect(source).toContain("MyRequestsEntityDirectoryPicker");
    expect(source).toContain("Adicionar selecionados");
    expect(source).not.toMatch(/>\s*Buscar\s*</);
    expect(source.match(/MyRequestsEntityDirectoryPicker/g)?.length).toBeGreaterThanOrEqual(3);
  });

  it("mantém party/carrier single e produtos multi", () => {
    expect(source).toContain("maxSelected={1}");
    expect(source).toContain("maxSelected={20}");
  });

  it("usa botões SC/ES para filial e layout denso de itens", () => {
    expect(source).toContain("my-requests-wizard-branch");
    expect(source).toContain("branchShortLabel");
    expect(source).toContain("my-requests-invoice-item__row");
    expect(source).not.toMatch(/label=\"Filial\"[\s\S]*SelectField/);
  });

  it("liga HelpTooltip/hints nos campos do wizard", () => {
    expect(source).toContain("HELP.partyType");
    expect(source).toContain("HELP.itemQuantity");
    expect(source).toContain("HELP.itemUnitPrice");
    expect(source).toContain("HELP.weightKg");
    expect(source).toContain("HELP.volumeCount");
    expect(source).toContain("HELP.observation");
    expect(source).toContain("hint: HELP.partySearch");
    expect(source).toContain("hint: HELP.productSearch");
    expect(source).toContain("hint: HELP.carrierSearch");
  });
});
