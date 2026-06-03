import { describe, expect, it } from "vitest";

import type { ChatStreamActivityEntry } from "../../data/api/chatTypes";

import {
  compactActivityLogForDisplay,
  fullActivityLogForDisplay,
  resolveActivityStatusMessage,
  resolveCurrentActivityLine,
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

  it("lista todas as etapas em ordem no painel expandido", () => {
    const full = fullActivityLogForDisplay([
      { id: "tool-1", phase: "tools", message: "Prefetch SA1", state: "done", at: 1 },
      { id: "tool-2", phase: "tools", message: "RAG", state: "done", at: 2 },
      { id: "think-1", phase: "think", message: "Pensando", state: "active", at: 3 },
    ]);

    expect(full).toHaveLength(3);
    expect(full.map((item) => item.id)).toEqual(["tool-1", "tool-2", "think-1"]);
  });

  it("mantém só a etapa mais recente por fase", () => {
    const compact = compactActivityLogForDisplay([
      { id: "think-1", phase: "think", message: "Pensando histórico", state: "done" },
      { id: "think-2", phase: "think", message: "Pensando rota OpenAPI", state: "active" },
      { id: "rag-search", phase: "rag", message: "Buscando base", state: "active" },
    ]);

    expect(compact).toHaveLength(2);
    expect(compact.find((item) => item.phase === "think")?.message).toBe(
      "Pensando rota OpenAPI",
    );
  });

  it("resolve linha ativa atual", () => {
    expect(
      resolveCurrentActivityLine([
        { id: "a", phase: "think", message: "Antigo", state: "done" },
        { id: "b", phase: "rag", message: "Buscando", state: "active" },
      ])?.message,
    ).toBe("Buscando");
  });

  it("prioriza headline da etapa ativa", () => {
    expect(
      resolveStreamingHeadline("Gerando resposta...", [
        { id: "1", message: "Consultando base...", state: "active" },
      ]),
    ).toBe("Consultando base...");
  });

  it("resolve status a partir da fase web_search", () => {
    expect(
      resolveActivityStatusMessage({
        id: "ws",
        phase: "web_search",
        message: "",
        state: "active",
      }),
    ).toBe("Pesquisando na internet...");
  });
});
