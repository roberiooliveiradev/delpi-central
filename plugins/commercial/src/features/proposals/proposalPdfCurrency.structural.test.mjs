#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Proposal PDF currency choice (R$/US$)", () => {
  it("detalhe pergunta a moeda antes de emitir o PDF", () => {
    const page = readFileSync(join(src, "features/proposals/ProposalDetailPage.tsx"), "utf8");
    assert.match(page, /useCommercialConfirmChoice/);
    assert.match(page, /confirmPdfCurrency/);
    assert.match(page, /pdfCurrencyTitle/);
    assert.match(page, /pdfCurrencyBrl/);
    assert.match(page, /pdfCurrencyUsd/);
    assert.match(page, /choice === "cancel"/);
    assert.match(page, /proposalPdfIdioma/);
    assert.match(page, /overrides\.idioma/);
    assert.match(page, /buildPdfOverrides\(currency\)/);
  });

  it("moeda US$ mapeia para idioma en (rótulos EN são canônicos na api)", () => {
    const util = readFileSync(join(src, "utils/proposalPdfCurrency.ts"), "utf8");
    assert.match(util, /currency === "usd"/);
    assert.match(util, /"en"/);
    // Sem conversão de valores nem mapa de labels duplicado no front.
    assert.doesNotMatch(util, /cotacao|exchange|rate/i);
    assert.doesNotMatch(util, /colunas_itens/);
  });

  it("provider expõe confirmChoice", () => {
    const provider = readFileSync(
      join(src, "app/CommercialConfirmDialogProvider.tsx"),
      "utf8",
    );
    assert.match(provider, /useCommercialConfirmChoice/);
    assert.match(provider, /context\.confirmChoice/);
  });
});
