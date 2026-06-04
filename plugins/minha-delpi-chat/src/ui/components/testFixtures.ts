import type { ChatToolCall } from "../../data/api/chatTypes";

/** Fixtures de toolCalls para testes — evita repetir casts em cada arquivo. */
export function fixtureToolCalls(calls: unknown[]): ChatToolCall[] {
  return calls as ChatToolCall[];
}
