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
const API = readFileSync(
  resolve(__dirname, "../api/productRegistrationApi.ts"),
  "utf8",
);
const CSS = readFileSync(resolve(__dirname, "../prc.css"), "utf8");
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
    // Rótulos de canal derivam do mapa canônico do plugin-ui (uma
    // única fonte) — não do literal duplicado local.
    expect(COPY).toMatch(/\.\.\.PRC_CHANNEL_LABELS/);
    expect(COPY).toMatch(/PRC_CHANNEL_LABELS,/);
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

describe("PrcDetailPage — avatar canônico (Core via BFF participants)", () => {
  it("resolve avatares pelo hook BFF e propaga ao histórico", () => {
    expect(SRC).toMatch(/useParticipantAvatarUrls/);
    expect(SRC).toMatch(/avatarByUserId=\{avatarByUserId\}/);
    expect(SRC).toMatch(/loadAvatar=\{loadConversationAvatar\}/);
  });

  it("hero também recebe a foto canônica via PrcPersonCell", () => {
    expect(SRC).toMatch(/avatarSrc=\{avatarByUserId\.get\(/);
    const TIMELINE = readFileSync(
      resolve(__dirname, "../components/PrcTimelineSection.tsx"),
      "utf8",
    );
    expect(TIMELINE).toMatch(/avatarByUserId\?:/);
    expect(TIMELINE).toMatch(/src=\{v\.actorUserId/);
    const CELL = readFileSync(
      resolve(__dirname, "../components/PrcPersonCell.tsx"),
      "utf8",
    );
    expect(CELL).toMatch(/avatarSrc\?:/);
    expect(CELL).toMatch(/src=\{avatarSrc/);
  });
});

describe("runAction — recibo de conclusão não substitui o detalhe", () => {
  /* Regressão: `complete` retorna recibo sem `allowedActions`; adotá-lo
   * como detalhe quebrava `detail.allowedActions.includes(...)` no
   * render seguinte (TypeError → tela branca em ?tab=verification). */
  it("só adota res.data como detalhe quando o payload tem forma de caso", () => {
    expect(SRC).toMatch(
      /"allowedActions" in res\.data[\s\S]{0,140}?setDetail\(res\.data\)/,
    );
  });

  it("contrato tipa o recibo de conclusão (não é PrcRequestDetail)", () => {
    expect(API).toMatch(/PrcCompletionReceipt/);
    expect(API).toMatch(
      /Envelope<PrcRequestDetail \| PrcCompletionReceipt>/,
    );
  });
});

describe("hero — posicionamento das ações", () => {
  it("ações do hero alinhadas à direita no desktop", () => {
    expect(CSS).toMatch(
      /\.engineering-prc__hero-actions \.engineering-prc__actions\s*\{[^}]*justify-content:\s*flex-end/,
    );
  });
});

describe("PrcActionBar — hierarquia, ícones e ajuda", () => {
  it("ações renderizam ícone Lucide ao lado do rótulo", () => {
    expect(ACTION_BAR).toMatch(/<Icon size=\{14\} aria-hidden \/>/);
    expect(ACTION_BAR).toMatch(/spec\.icon/);
  });

  it("ações levam ajuda contextual via title", () => {
    expect(ACTION_BAR).toMatch(/spec\.help/);
    // Automação gateada troca o hint por aviso honesto de gate.
    expect(ACTION_BAR).toMatch(/publishGated/);
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

  it("publish_totvs — automação com destaque acentuado e ícone", () => {
    const block = /action: "publish_totvs",[\s\S]*?icon: CloudUpload,[\s\S]*?accent: true/;
    expect(SPECS).toMatch(block);
    expect(ACTION_BAR).toMatch(/engineering-prc__action--accent/);
    expect(ACTION_BAR).toMatch(/publishGated/);
    expect(API).toMatch(/totvsPublishEnabled\?: boolean/);
    expect(API).toMatch(/totvsPublish\?: string/);
  });
});
