import { describe, expect, it, vi } from "vitest";

import {
  isAttachmentIndexPending,
  isTerminalAttachmentStatus,
  waitForSessionAttachmentIndexed,
} from "./workspaceFileIngestPolling";

vi.mock("./api/chatApi", () => ({
  fetchChatSessionAttachments: vi.fn(),
}));

import { fetchChatSessionAttachments } from "./api/chatApi";

describe("workspaceFileIngestPolling", () => {
  it("detecta status pendente de indexação", () => {
    expect(isAttachmentIndexPending("indexing")).toBe(true);
    expect(isAttachmentIndexPending("uploaded")).toBe(true);
    expect(isAttachmentIndexPending("indexed")).toBe(false);
  });

  it("aguarda até o anexo sair do estado indexing", async () => {
    vi.mocked(fetchChatSessionAttachments)
      .mockResolvedValueOnce([
        {
          id: "att-1",
          status: "indexing",
        } as never,
      ])
      .mockResolvedValueOnce([
        {
          id: "att-1",
          status: "indexed",
          metadata: { readingStatus: "Indexado" },
        } as never,
      ]);

    const result = await waitForSessionAttachmentIndexed(
      "session-1",
      "att-1",
      {},
      { intervalMs: 1, timeoutMs: 100 },
    );

    expect(result?.status).toBe("indexed");
    expect(fetchChatSessionAttachments).toHaveBeenCalledTimes(2);
  });

  it("identifica status terminal", () => {
    expect(isTerminalAttachmentStatus("indexed")).toBe(true);
    expect(isTerminalAttachmentStatus("index_failed")).toBe(true);
    expect(isTerminalAttachmentStatus("indexing")).toBe(false);
  });
});
