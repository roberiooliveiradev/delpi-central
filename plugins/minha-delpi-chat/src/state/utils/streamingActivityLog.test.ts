import { describe, expect, it } from "vitest";

import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";

import {
  resolveStreamingHeadline,
  upsertStreamingActivityEntry,
} from "./streamingActivityLog";

describe("streamingActivityLog", () => {
  it("atualiza entrada existente pelo id", () => {
    const initial: ChatStreamActivityEntry[] = [
      {
        id: "rag-search",
        message: "Buscando...",
        state: "active",
      },
    ];

    const next = upsertStreamingActivityEntry(initial, {
      id: "rag-search",
      message: "Encontrado 2 trechos",
      state: "done",
    });

    expect(next).toHaveLength(1);
    expect(next[0]?.state).toBe("done");
  });

  it("prioriza headline da etapa ativa", () => {
    expect(
      resolveStreamingHeadline("Gerando resposta...", [
        { id: "1", message: "Consultando base...", state: "active" },
      ]),
    ).toBe("Consultando base...");
  });
});
