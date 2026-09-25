import { describe, expect, it, vi } from "vitest";

import {
  commitOpsAndApplyAck,
  createMutationGenerationGate,
} from "./mutationAckGeneration";

vi.mock("./presentationMutationClient", () => ({
  commitPresentationOps: vi.fn(),
  commitUpsertBlocks: vi.fn(),
}));

import { commitPresentationOps } from "./presentationMutationClient";

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
});
