import { describe, expect, it } from "vitest";
import {
  detectActiveMention,
  filterMentionCandidates,
  insertMentionToken,
  splitCommentMentionSegments,
} from "./commentMentions";

describe("commentMentions", () => {
  it("detecta @ativo sob o cursor", () => {
    expect(detectActiveMention("Olá @mar", 8)).toEqual({
      query: "mar",
      start: 4,
      end: 8,
    });
    expect(detectActiveMention("Olá maria", 9)).toBeNull();
  });

  it("insere token de menção com espaço", () => {
    const result = insertMentionToken("Olá @mar", 8, 4, "Maria Silva");
    expect(result.nextValue).toBe("Olá @Maria Silva ");
    expect(result.nextCursor).toBe("Olá @Maria Silva ".length);
  });

  it("filtra candidatos por nome/email e exclui já mencionados", () => {
    const items = [
      { id: "1", name: "Maria Silva", email: "maria@delpi.com.br" },
      { id: "2", name: "João", email: "joao@delpi.com.br" },
    ];
    expect(filterMentionCandidates(items, "mar", new Set(["2"]))).toEqual([
      items[0],
    ]);
  });

  it("divide texto destacando menções sem o @", () => {
    expect(splitCommentMentionSegments("Oi @Maria Silva, ok?")).toEqual([
      { type: "text", value: "Oi " },
      { type: "mention", value: "Maria Silva" },
      { type: "text", value: ", ok?" },
    ]);
  });
});
