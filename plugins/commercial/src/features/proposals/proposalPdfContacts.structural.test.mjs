#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Proposal PDF contacts (E7)", () => {
  it("detalhe edita contato só no PDF revisável com Commercial*", () => {
    const page = readFileSync(join(src, "features/proposals/ProposalDetailPage.tsx"), "utf8");
    assert.match(page, /getAccountContactsBundle/);
    assert.match(page, /CommercialSelectField/);
    assert.match(page, /CommercialTextField/);
    assert.match(page, /pdfContatoNome/);
    assert.match(page, /pdfContatoDepartamento/);
    assert.match(page, /pdfContatoEmail/);
    assert.match(page, /pdfContatoTelefone/);
    assert.match(page, /buildProposalPdfContactOptions/);
    assert.match(page, /buildPdfOverrides/);
    assert.match(page, /pdfContactFieldsHint|PDF revisável/);
    assert.match(page, /CommercialTextAreaField/);
    // Card Contato da ficha permanece DetailFieldGrid (somente leitura).
    assert.match(page, /title="Contato"/);
    assert.match(page, /CommercialDetailFieldGrid/);
    assert.doesNotMatch(page, /\bEmptyState\b|\bSectionCard\b/);
  });

  it("resolve expõe departamento e telefone nas opções", () => {
    const util = readFileSync(join(src, "utils/resolveProposalPdfContact.ts"), "utf8");
    assert.match(util, /departamento:/);
    assert.match(util, /telefone:/);
    assert.match(util, /phone_e164/);
    assert.match(util, /role_title/);
  });
});
