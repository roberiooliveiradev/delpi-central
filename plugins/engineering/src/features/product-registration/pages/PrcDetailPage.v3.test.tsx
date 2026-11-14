/** UX V3 — regressões estruturais do detalhe PRC: hero sem grade de
 * metadados, identidade por avatar, responsável condicional, popover
 * «Informações» via portal oficial, alerta de verificação acionável e
 * alvo estável para reexecução de conclusão. */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

const SRC = readFileSync(resolve(__dirname, "PrcDetailPage.tsx"), "utf8");
const COPY = readFileSync(resolve(__dirname, "../prcCopy.ts"), "utf8");
const ACTION_BAR = readFileSync(
  resolve(__dirname, "../components/PrcActionBar.tsx"),
  "utf8",
);
const SPECS = readFileSync(
  resolve(__dirname, "../components/prcActionSpecs.ts"),
  "utf8",
);

describe("PrcDetailPage — hero UX V3", () => {
  it("não renderiza a grade redundante de metadados no hero", () => {
    expect(SRC).not.toMatch(/EngineeringDetailFieldGrid/);
    expect(SRC).not.toMatch(/hero-meta"|hero-meta\s/);
  });

  it("solicitante e responsável usam avatar via PrcPersonCell", () => {
    expect(SRC).toMatch(/PrcPersonCell[\s\S]*subject=\{detail\.requester\.subject\}/);
    expect(SRC).toMatch(/subject=\{detail\.assignedTo\}/);
    expect(SRC).toMatch(/displayName=\{detail\.assignedToDisplayName\}/);
  });

  it("responsável é condicional — sem bloco vazio quando ausente", () => {
    expect(SRC).toMatch(/\{detail\.assignedTo \? \(/);
    expect(SRC).not.toMatch(/Responsável não identificado/);
  });

  it("§56 — nenhum chip de revisão base em solicitação aberta", () => {
    expect(SRC).not.toMatch(/Revisão base/);
    expect(SRC).not.toMatch(/baseRevision/);
  });

  it("§56 — concluída mostra revisão gerada ou no-op honesto", () => {
    expect(SRC).toMatch(/Revisão técnica gerada: V/);
    expect(SRC).toMatch(/publishedRevision\.revisionNumber/);
    expect(SRC).toMatch(/Concluída sem nova revisão técnica/);
  });

  it("popover «Informações» usa o portal ancorado oficial com escopo do MFE", () => {
    expect(SRC).toMatch(/EngineeringAnchoredPanel/);
    expect(SRC).toMatch(/portalScopeClassName=\{ENGINEERING_PORTAL_SCOPE\}/);
    expect(SRC).toMatch(/aria-label="Informações da solicitação"/);
    expect(SRC).toMatch(/onDismiss=\{\(\) => setInfoOpen\(false\)\}/);
  });

  it("metadados de auditoria ficam no popover, não no hero", () => {
    expect(SRC).toMatch(/Identificador no canal de origem/);
    expect(SRC).toMatch(/Última atualização/);
    expect(SRC).toMatch(/Versão interna do atendimento/);
    expect(SRC).toMatch(/não corresponde necessariamente ao número interno/);
  });

  it("canal corporativo é apresentado como Minhas Solicitações", () => {
    expect(COPY).toMatch(/my_requests: "Minhas Solicitações"/);
    expect(COPY).toMatch(/"my-requests": "Minhas Solicitações"/);
    expect(COPY).not.toMatch(/Canal corporativo \(My Requests\)/);
  });

  it("alerta de verificação bloqueante direciona à aba Verificação TOTVS", () => {
    expect(SRC).toMatch(/verify-alert/);
    expect(SRC).toMatch(/PRC_RESULT_VARIANTS\[verificationResult\] === "danger"/);
    expect(SRC).toMatch(/Ver diagnóstico/);
    expect(SRC).toMatch(/selectTab\("verification"\)/);
  });

  it("reexecução de conclusão usa ref estável, não querySelector frágil", () => {
    expect(SRC).not.toMatch(/document\s*\.?\s*querySelector\(/);
    expect(SRC).toMatch(/actionsRef\.current\?\.scrollIntoView/);
  });
});

describe("PrcActionBar — hierarquia, ícones e ajuda", () => {
  it("ações renderizam ícone Lucide ao lado do rótulo", () => {
    expect(ACTION_BAR).toMatch(/<Icon size=\{14\} aria-hidden \/>/);
    expect(ACTION_BAR).toMatch(/spec\.icon/);
  });

  it("ações levam ajuda contextual via title", () => {
    expect(ACTION_BAR).toMatch(/title=\{spec\.help\}/);
  });

  it("ação destrutiva recebe classe visual distinta", () => {
    expect(ACTION_BAR).toMatch(/engineering-prc__action--danger/);
  });

  it("catálogo define ícone e ajuda para as ações principais", () => {
    for (const action of [
      "complete",
      "return_for_correction",
      "reject",
      "resubmit_correction",
      "edit_draft",
    ]) {
      const block = new RegExp(
        `action: "${action}",[\\s\\S]*?icon: \\w+,[\\s\\S]*?help: "`,
      );
      expect(SPECS).toMatch(block);
    }
  });
});
