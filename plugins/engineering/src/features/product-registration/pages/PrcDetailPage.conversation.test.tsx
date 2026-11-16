/** PRC-CONVERSATION — contrato estrutural: conversa na aba Histórico,
 * adapter PRC e scope do MFE, sem avatar fictício. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "PrcDetailPage.tsx"),
  "utf-8",
);

describe("PrcDetailPage — conversa PRC (estrutural)", () => {
  it("monta ConversationPanel do kit com adapter PRC na aba history", () => {
    expect(SRC).toMatch(/import \{ ConversationPanel \} from "@delpi\/plugin-ui\/index"/);
    expect(SRC).toMatch(/prcConversationApi/);
    const history = SRC.indexOf('tab === "history"');
    const panel = SRC.indexOf("<ConversationPanel");
    expect(panel).toBeGreaterThan(history);
    expect(SRC).toMatch(/api=\{prcConversationApi\}/);
    expect(SRC).toMatch(/requestId=\{detail\.id\}/);
    expect(SRC).toMatch(/sectionTitle="Conversa sobre a solicitação"/);
  });

  it("terminal congela a conversa (policy backend espelhada na UI)", () => {
    expect(SRC).toMatch(/conversationFrozen=\{[\s\S]*completed[\s\S]*rejected/);
    expect(SRC).not.toMatch(/loadAvatar=/);
  });
});
