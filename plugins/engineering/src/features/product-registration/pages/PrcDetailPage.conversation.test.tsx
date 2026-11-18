/** PRC-CONVERSATION — contrato estrutural: conversa empilhada na Ficha
 * técnica (decisão PO PRC-UX-DETAIL-THREE-TABS-STACKED-CONVERSATION-01),
 * adapter PRC e scope do MFE, sem avatar fictício. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "PrcDetailPage.tsx"),
  "utf-8",
);

describe("PrcDetailPage — conversa PRC (estrutural)", () => {
  it("monta ConversationPanel do kit com adapter PRC na Ficha técnica", () => {
    expect(SRC).toMatch(
      /import \{[^}]*ConversationPanel[^}]*\} from "@delpi\/plugin-ui\/index"/,
    );
    expect(SRC).toMatch(/prcConversationApi/);
    const draft = SRC.indexOf('tab === "draft"');
    const attachments = SRC.indexOf("<PrcAttachmentsSection");
    const panel = SRC.indexOf("<ConversationPanel");
    const exchange = SRC.indexOf("<PrcInformationExchangePanel");
    const timeline = SRC.indexOf("<PrcTimelineSection");
    expect(panel).toBeGreaterThan(draft);
    expect(panel).toBeGreaterThan(attachments);
    expect(exchange).toBeGreaterThan(panel);
    expect(timeline).toBeGreaterThan(exchange);
    expect(SRC).toMatch(/api=\{prcConversationApi\}/);
    expect(SRC).toMatch(/requestId=\{detail\.id\}/);
    expect(SRC).toMatch(/sectionTitle="Conversa sobre a solicitação"/);
  });

  it("três abas apenas — Histórico absorvido pela Ficha técnica", () => {
    expect(SRC).not.toContain('key: "history"');
    expect(SRC).not.toContain('tab === "history"');
    const tabsDecl = SRC.slice(
      SRC.indexOf("const TABS"),
      SRC.indexOf("];", SRC.indexOf("const TABS")),
    );
    expect(tabsDecl.match(/\{ key: "/g)).toHaveLength(3);
    expect(SRC).toMatch(/title="Histórico da solicitação"/);
  });

  it("terminal congela a conversa (policy backend espelhada na UI)", () => {
    expect(SRC).toMatch(/conversationFrozen=\{[\s\S]*completed[\s\S]*rejected/);
  });

  it("avatar do autor usa o resolvedor governado do BFF (Core)", () => {
    // PRC-AUDIT — foto canônica do Portal via
    // engineering-api /v1/participants (S2S → Core); ausente → iniciais.
    expect(SRC).toMatch(/loadAvatar=\{loadConversationAvatar\}/);
    expect(SRC).toMatch(/downloadParticipantAvatarBlob/);
  });

  it("FIX-F01 — evento realtime do caso refaz a leitura via refreshKey", () => {
    expect(SRC).toMatch(/refreshKey=\{conversationRefreshKey\}/);
    /* bump dentro do callback do usePrcCaseSync (escopo do caso) e
     * antes do gate de edição — rascunho/anexo do composer
     * preservados pelo reload interno do painel. */
    const sync = SRC.indexOf("usePrcCaseSync(");
    const bump = SRC.indexOf("setConversationRefreshKey((key) => key + 1)");
    const editGate = SRC.indexOf("setRemoteChanged(true)", sync);
    expect(bump).toBeGreaterThan(sync);
    expect(bump).toBeLessThan(editGate);
  });
});
