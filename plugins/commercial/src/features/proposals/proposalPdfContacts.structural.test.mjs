#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Proposal PDF contacts (E5.S2)", () => {
  it("detalhe usa select de contatos e não inputs raw", () => {
    const page = readFileSync(join(src, "features/proposals/ProposalDetailPage.tsx"), "utf8");
    assert.match(page, /getAccountContactsBundle/);
    assert.match(page, /CommercialSelectField/);
    assert.match(page, /buildProposalPdfContactOptions/);
    assert.match(page, /CommercialTextAreaField/);
    assert.doesNotMatch(page, /pdfContatoNome|pdfContatoEmail/);
    assert.doesNotMatch(page, /type="email"/);
    assert.doesNotMatch(page, /<input/);
    assert.doesNotMatch(page, /\bEmptyState\b|\bSectionCard\b/);
  });
});
