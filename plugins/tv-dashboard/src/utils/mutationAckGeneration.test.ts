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
import {
  createPendingProjectionRegistry,
  pendingBlockKey,
} from "./pendingMutationProjection";

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

  it("027: marca entidades cobertas no dispatch e libera no ack", async () => {
    const gate = createMutationGenerationGate();
    const registry = createPendingProjectionRegistry();
    const refresh = vi.fn();
    const baseline = { version: 4, blocks: [{ id: "a", frame: { x: 40 } }] };
    const live = { version: 4, blocks: [{ id: "a", frame: { x: 8 } }] };
    const canonical = { version: 4, blocks: [{ id: "a", frame: { x: 8 } }] };
    vi.mocked(commitUpsertBlocks).mockResolvedValueOnce(canonical as never);

    const result = await ackUpsertBlocksWithGeneration({
      playlistId: "p",
      slideId: "s",
      blocks: [{ id: "a", frame: { x: 8 } }],
      gate,
      applyAck: vi.fn(),
      pending: {
        registry,
        getBaseline: () => baseline as never,
        getLive: () => live as never,
        refresh,
      },
    });

    expect(result).toEqual(canonical);
    // Mark aconteceu no dispatch e foi liberado após o ack.
    expect(registry.hasPending()).toBe(false);
    expect(refresh).toHaveBeenCalled();
  });

  it("027: mantém marks em falha — autosave segue no baseline até reconciliar", async () => {
    const gate = createMutationGenerationGate();
    const registry = createPendingProjectionRegistry();
    const baseline = { version: 4, blocks: [{ id: "a", frame: { x: 40 } }] };
    vi.mocked(commitUpsertBlocks).mockRejectedValueOnce(new Error("HTTP 500"));

    const result = await ackUpsertBlocksWithGeneration({
      playlistId: "p",
      slideId: "s",
      blocks: [{ id: "a", frame: { x: 8 } }],
      gate,
      applyAck: vi.fn(),
      pending: {
        registry,
        getBaseline: () => baseline as never,
        getLive: () => baseline as never,
      },
    });

    expect(result).toBeNull();
    // Marks permanecem: sem clear autoritativo a entidade não vaza pelo PATCH.
    expect(registry.get(pendingBlockKey("a"))).toBeDefined();
  });

  it("027: ops derivam cobertura de patch_native_config e blockIds", async () => {
    const gate = createMutationGenerationGate();
    const registry = createPendingProjectionRegistry();
    const baseline = { version: 4, background: { type: "color", value: "#111" } };
    let resolveOps: ((v: unknown) => void) | undefined;
    vi.mocked(commitPresentationOps).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveOps = resolve;
      }) as never,
    );

    const pendingPromise = commitOpsAndApplyAck({
      playlistId: "p",
      slideId: "s",
      ops: [
        { op: "patch_native_config", patch: { background: { type: "color" } } },
        { op: "align_blocks", blockIds: ["a", "b"], command: "left" },
      ],
      gate,
      applyAck: vi.fn(),
      pending: { registry, getBaseline: () => baseline as never },
    });

    // Durante a janela in-flight a cobertura está marcada.
    expect(registry.get("field:background")).toBeDefined();
    expect(registry.get(pendingBlockKey("a"))).toBeDefined();
    expect(registry.get(pendingBlockKey("b"))).toBeDefined();

    resolveOps?.({ blocks: [] });
    await pendingPromise;
    expect(registry.hasPending()).toBe(false);
  });
});
