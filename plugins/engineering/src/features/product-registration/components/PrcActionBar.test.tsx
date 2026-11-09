import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("PrcActionBar — PRC-REF-017", () => {
  it("CREATE usa label de código do produto criado e hint de cadastro manual", () => {
    const src = readFileSync(join(here, "PrcActionBar.tsx"), "utf8");
    expect(src).toMatch(/Código do produto criado no TOTVS/);
    expect(src).toMatch(
      /Informe o código oficial atribuído ao produto após o cadastro manual no TOTVS/,
    );
    expect(src).toMatch(/requestType/);
    expect(src).toMatch(/readOnly=\{isUpdate\}/);
  });

  it("UPDATE trava código no baseline e bloqueia edição no diálogo", () => {
    const src = readFileSync(join(here, "PrcActionBar.tsx"), "utf8");
    expect(src).toMatch(/Código oficial TOTVS \(baseline\)/);
    expect(src).toMatch(/Código travado no baseline D15/);
    expect(src).toMatch(/p && !isUpdate/);
  });

  it("não permite confirmar CREATE sem código (validação client-side)", () => {
    const src = readFileSync(join(here, "PrcActionBar.tsx"), "utf8");
    expect(src).toMatch(/!isUpdate && !code/);
    expect(src).toMatch(/Informe o código oficial atribuído ao produto/);
  });

  it("request_information abre formulário multi-pergunta (PRC-REF-019)", () => {
    const src = readFileSync(join(here, "PrcActionBar.tsx"), "utf8");
    expect(src).toMatch(/spec\.needsQuestions/);
    expect(src).toMatch(/<PrcRequestInformationModal/);
    expect(src).toMatch(/questions, message, pendingFields/);
    const modal = readFileSync(
      join(here, "PrcRequestInformationModal.tsx"),
      "utf8",
    );
    expect(modal).toMatch(/PRC_INFO_COPY\.addQuestion/);
    expect(modal).toMatch(/validateInfoQuestions/);
  });
});
