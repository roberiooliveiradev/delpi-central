/** PRC-CONVERSATION — contrato estrutural: conversa montada na aba
 * Histórico do caso, com adapter PRC e scope do MFE. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "PrcCasePage.tsx"),
  "utf-8",
);

describe("PrcCasePage — conversa PRC (estrutural)", () => {
  it("monta ConversationPanel do kit com adapter PRC", () => {
    expect(SRC).toMatch(/import \{ ConversationPanel \} from "@delpi\/plugin-ui\/index"/);
    expect(SRC).toMatch(/import \{ prcConversationApi \} from "\.\/prcConversationApi"/);
    expect(SRC).toMatch(/<ConversationPanel/);
    expect(SRC).toMatch(/api=\{prcConversationApi\}/);
    expect(SRC).toMatch(/requestId=\{detail\.id\}/);
    expect(SRC).toMatch(/sectionTitle="Conversa sobre a solicitação"/);
  });

  it("conversa fica na aba history e respeita estado terminal", () => {
    const history = SRC.indexOf('tab === "history"');
    const panel = SRC.indexOf("<ConversationPanel");
    expect(history).toBeGreaterThan(-1);
    expect(panel).toBeGreaterThan(history);
    expect(SRC).toMatch(/conversationFrozen=\{conversationFrozen\}/);
    expect(SRC).toMatch(/status === "completed" \|\| detail\?\.status === "rejected"/);
  });

  it("avatar vem do BFF próprio (requests-api → Core), nunca payload", () => {
    expect(SRC).toMatch(/downloadParticipantAvatarBlob/);
    expect(SRC).toMatch(/loadAvatar=\{loadConversationAvatar\}/);
  });
});
