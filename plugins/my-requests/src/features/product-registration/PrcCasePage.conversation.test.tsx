/** PRC-CONVERSATION — contrato estrutural: conversa montada como
 * seção vertical da página única do caso, com adapter PRC e scope do
 * MFE (P3-FIX RQ-01). */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "PrcCasePage.tsx"),
  "utf-8",
);

describe("PrcCasePage — conversa PRC (estrutural)", () => {
  it("monta ConversationPanel do kit com adapter PRC", () => {
    expect(SRC).toMatch(/import \{[^}]*ConversationPanel[^}]*\} from "@delpi\/plugin-ui\/index"/);
    expect(SRC).toMatch(/import \{ prcConversationApi \} from "\.\/prcConversationApi"/);
    expect(SRC).toMatch(/<ConversationPanel/);
    expect(SRC).toMatch(/api=\{prcConversationApi\}/);
    expect(SRC).toMatch(/requestId=\{detail\.id\}/);
    expect(SRC).toMatch(/sectionTitle="Conversa sobre a solicitação"/);
  });

  it("conversa é seção da página única, após ficha e antes da linha do tempo", () => {
    const sheet = SRC.indexOf("<PrcTechnicalSheetView");
    const panel = SRC.indexOf("<ConversationPanel");
    const timeline = SRC.indexOf("Linha do tempo");
    expect(panel).toBeGreaterThan(sheet);
    expect(timeline).toBeGreaterThan(panel);
    expect(SRC).toMatch(/conversationFrozen=\{conversationFrozen\}/);
    expect(SRC).toMatch(/status === "completed" \|\| detail\?\.status === "rejected"/);
  });

  it("avatar vem do BFF próprio (requests-api → Core), nunca payload", () => {
    expect(SRC).toMatch(/downloadParticipantAvatarBlob/);
    expect(SRC).toMatch(/loadAvatar=\{loadConversationAvatar\}/);
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

  it("EXPANDABLE — conversa oferece expansão em modal host-contained", () => {
    /* Mesmo ConversationPanel compartilhado, opt-in `expandable`, com
     * contexto da solicitação no cabeçalho do modal. */
    expect(SRC).toMatch(/expandable/);
    expect(SRC).toMatch(/expandDialogDescription=\{/);
    expect(SRC).toMatch(/detail\.id\.slice\(0,\s*8\)/);
  });
});
