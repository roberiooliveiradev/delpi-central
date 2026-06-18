import { describe, expect, it } from "vitest";

import {
  CHAT_SESSION_DRAG_MIME,
  readChatSessionDragId,
  setChatSessionDragData,
} from "./chatSessionDragDrop";

describe("chatSessionDragDrop", () => {
  it("grava e lê o id da sessão no dataTransfer", () => {
    const dataTransfer = {
      store: {} as Record<string, string>,
      effectAllowed: "none",
      setData(type: string, value: string) {
        this.store[type] = value;
      },
      getData(type: string) {
        return this.store[type] ?? "";
      },
    } as unknown as DataTransfer;

    setChatSessionDragData(dataTransfer, "session-123");

    expect(dataTransfer.effectAllowed).toBe("move");
    expect(readChatSessionDragId(dataTransfer)).toBe("session-123");
    expect(dataTransfer.getData(CHAT_SESSION_DRAG_MIME)).toBe("session-123");
  });
});
