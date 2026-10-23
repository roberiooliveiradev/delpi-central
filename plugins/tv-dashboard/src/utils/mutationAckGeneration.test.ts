import { describe, expect, it, vi } from "vitest";

import {
  ackUpsertBlocksWithGeneration,
  commitOpsAndApplyAck,
  createMutationGenerationGate,
} from "./mutationAckGeneration";

vi.mock("./presentationMutationClient", () => ({
  commitPresentationOps: vi.fn(),
  commitUpsertBlocks: vi.fn(),
}));

import {
  commitPresentationOps,
  commitUpsertBlocks,
} from "./presentationMutationClient";

describe("mutationAckGeneration", () => {
  it("descarta ack stale quando houve mutação mais nova", async () => {
    const gate = createMutationGenerationGate();
    const applyAck = vi.fn();
    const slow = new Promise<{ blocks: [] }>((resolve) => {
      setTimeout(() => resolve({ blocks: [] }), 30);
    });
    vi.mocked(commitPresentationOps).mockReturnValueOnce(slow as never);

    const first = commitOpsAndApplyAck({
      playlistId: "p",
      slideId: "s",
      ops: [{ op: "transform_text_case", blockId: "a", mode: "upper" }],
      gate,
      applyAck,
    });

    gate.next(); // simulate newer mutation

    const result = await first;
    expect(result).toBeNull();
    expect(applyAck).not.toHaveBeenCalled();
  });

  it("aplica ack quando generation ainda é atual", async () => {
    const gate = createMutationGenerationGate();
    const applyAck = vi.fn();
    const canonical = { version: 5, blocks: [{ id: "a", type: "text", content: "X" }] };
    vi.mocked(commitPresentationOps).mockResolvedValueOnce(canonical as never);

    const result = await commitOpsAndApplyAck({
      playlistId: "p",
      slideId: "s",
      ops: [{ op: "transform_text_case", blockId: "a", mode: "upper" }],
      gate,
      applyAck,
    });

    expect(result).toEqual(canonical);
    expect(applyAck).toHaveBeenCalledWith(canonical);
  });

  it("propaga writeGuard/onCommitted ao commit e reporta onError em falha", async () => {
    const gate = createMutationGenerationGate();
    const applyAck = vi.fn();
    const onCommitted = vi.fn();
    const onError = vi.fn();
    const writeGuard = { expectedRevision: 42, clientId: "c-1" };
    vi.mocked(commitPresentationOps).mockResolvedValueOnce({ blocks: [] } as never);

    await commitOpsAndApplyAck({
      playlistId: "p",
      slideId: "s",
      ops: [{ op: "transform_text_case", blockId: "a", mode: "upper" }],
      gate,
      applyAck,
      writeGuard,
      onCommitted,
      onError,
    });

    expect(commitPresentationOps).toHaveBeenCalledWith(
      expect.objectContaining({ writeGuard, onCommitted }),
    );

    const conflict = new Error("409 REVISION_CONFLICT");
    vi.mocked(commitUpsertBlocks).mockRejectedValueOnce(conflict);
    const result = await ackUpsertBlocksWithGeneration({
      playlistId: "p",
      slideId: "s",
      blocks: [{ id: "a" }],
      gate,
      applyAck,
      writeGuard,
      onCommitted,
      onError,
    });
    expect(result).toBeNull();
    // 025-R2 — o erro carrega a identidade da mutação que falhou, não da
    // seleção atual do editor.
    expect(onError).toHaveBeenCalledWith(conflict, {
      playlistId: "p",
      slideId: "s",
    });
    // Ack rejeitado nunca aplica estado canônico.
    expect(applyAck).toHaveBeenCalledTimes(1);
  });

  it("025-R2: onError de ops carrega playlistId/slideId do dispatch", async () => {
    const gate = createMutationGenerationGate();
    const applyAck = vi.fn();
    const onError = vi.fn();
    const failure = new Error("HTTP 500");
    vi.mocked(commitPresentationOps).mockRejectedValueOnce(failure);

    const result = await commitOpsAndApplyAck({
      playlistId: "pl-A",
      slideId: "slide-A",
      ops: [{ op: "align_blocks", blockIds: ["a"], command: "left" }],
      gate,
      applyAck,
      onError,
    });

    expect(result).toBeNull();
    expect(onError).toHaveBeenCalledWith(failure, {
      playlistId: "pl-A",
      slideId: "slide-A",
    });
    expect(applyAck).not.toHaveBeenCalled();
  });
});
