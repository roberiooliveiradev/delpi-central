import { act, renderHook } from "@testing-library/react";
import { useCallback, useRef } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

vi.mock("../../api/tvDashboardApi", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/tvDashboardApi")>();
  return { ...mod, applyPresentationMutations: vi.fn() };
});

import { applyPresentationMutations } from "../../api/tvDashboardApi";
import { useComunicadoEditorBlocks } from "./useComunicadoEditorBlocks";
import { snapshotConfig, useComunicadoEditorHistory } from "./useComunicadoEditorHistory";

/**
 * VISTA-TV-EDITOR-LOCAL-VISUAL-PROJECTION-025 — alinhar/distribuir/z-order
 * projetam o resultado canônico no palco ANTES do ACK: a geometria local é a
 * mesma portada pelo backend (`block_layout_service`), e a persistência segue
 * o caminho já estabelecido de move/resize/sameSize — `upsert_block` do
 * resultado projetado + autosave, nunca `align_blocks`/`reorder_block_z`
 * (que não reconciliam conectores e divergem nos valores de zIndex).
 */

type MutationOps = Array<{ op: string; [key: string]: unknown }>;

const mutationsMock = vi.mocked(applyPresentationMutations);

function makeFakeMutationServer(initial: ComunicadoConfig) {
  let persisted = JSON.parse(JSON.stringify(initial)) as Record<string, unknown>;
  const deferred: Array<{
    ops: MutationOps;
    resolve: (result: { nativeConfig: Record<string, unknown> }) => void;
    reject: (error: unknown) => void;
  }> = [];

  const applyOps = (ops: MutationOps) => {
    const cfg = JSON.parse(JSON.stringify(persisted)) as Record<string, unknown> & {
      blocks?: Array<Record<string, unknown>>;
    };
    for (const op of ops) {
      if (op.op === "upsert_block") {
        const block = op.block as Record<string, unknown>;
        const blocks = (cfg.blocks ??= []);
        const index = blocks.findIndex((item) => item.id === block.id);
        if (index >= 0) blocks[index] = block;
        else blocks.push(block);
      }
    }
    persisted = cfg;
    return { nativeConfig: JSON.parse(JSON.stringify(persisted)) };
  };

  return {
    persisted: () => persisted,
    deferred,
    applyOps,
    immediate: vi.fn((_p: string, _s: string, ops: MutationOps) =>
      Promise.resolve(applyOps(ops)),
    ),
    controlled: vi.fn(
      (_p: string, _s: string, ops: MutationOps) =>
        new Promise<{ nativeConfig: Record<string, unknown> }>((resolve, reject) => {
          deferred.push({ ops, resolve, reject });
        }),
    ),
  };
}

function twoBlockConfig(): ComunicadoConfig {
  return {
    version: 2,
    background: { type: "color", value: "#ffffff" },
    blocks: [
      {
        id: "a1",
        type: "text",
        content: "A",
        contentRuns: [{ text: "A" }],
        frame: { x: 10, y: 10, w: 30, h: 10 },
        style: { zIndex: 1 },
      },
      {
        id: "b1",
        type: "text",
        content: "B",
        contentRuns: [{ text: "B" }],
        frame: { x: 50, y: 40, w: 30, h: 10 },
        style: { zIndex: 2 },
      },
      {
        id: "c1",
        type: "text",
        content: "C",
        contentRuns: [{ text: "C" }],
        frame: { x: 80, y: 70, w: 30, h: 10 },
        style: { zIndex: 3 },
      },
    ] as unknown as ComunicadoConfig["blocks"],
  };
}

function renderEditor(args: {
  playlistId?: string;
  slideId?: string;
  config: ComunicadoConfig;
}) {
  const persistedPayloads: ComunicadoConfig[] = [];
  const selectedIdsRef = { current: [] as string[] };
  const hook = renderHook(() => {
    const configRef = useRef<ComunicadoConfig>(args.config);
    const removeSelectedRef = useRef(() => {});
    const updateBlockTextFieldsRef = useRef(() => {});
    const applyConfig = useCallback(
      (next: ComunicadoConfig, options?: { persist?: boolean }) => {
        configRef.current = next;
        if (options?.persist !== false) {
          persistedPayloads.push(snapshotConfig(next));
        }
      },
      [],
    );
    const history = useComunicadoEditorHistory({
      configRef,
      applyConfig,
      deckHistory: null,
    });
    const blocks = useComunicadoEditorBlocks({
      playlistId: args.playlistId,
      slideId: args.slideId,
      configRef,
      commitWithHistory: history.commitWithHistory,
      applyServerConfig: history.applyServerConfig,
      selectedIds: selectedIdsRef.current,
      getActionSelectedIds: () => selectedIdsRef.current,
      selectedId: selectedIdsRef.current[0] ?? null,
      selected: null,
      selectedBlocks: [],
      selectedChartPart: null,
      selectedTablePart: null,
      selectedKpiPart: null,
      selectedInputPart: null,
      editingChartPart: null,
      editingKpiPart: null,
      setSelectedId: (id) => {
        selectedIdsRef.current = id ? [id] : [];
      },
      selectBlocksByIds: (ids) => {
        selectedIdsRef.current = ids;
      },
      setSelectedChartPart: vi.fn(),
      setEditingChartPart: vi.fn(),
      setSelectedTablePart: vi.fn(),
      setSelectedKpiPart: vi.fn(),
      setEditingKpiPart: vi.fn(),
      setLastDataDisplayMode: vi.fn(),
      setDataPanelOpen: vi.fn(),
      setDataPanelIntent: vi.fn(),
      setDataCatalogModalOpen: vi.fn(),
      setDataCatalogAnchor: vi.fn(),
      setDataCatalogMode: vi.fn(),
      setShapeMenuOpen: vi.fn(),
      setRibbonTabRequest: vi.fn(),
      removeSelectedRef,
      updateBlockTextFieldsRef,
    });
    return { configRef, history, blocks };
  });
  return { ...hook, persistedPayloads, selectedIdsRef };
}

const frameOf = (config: ComunicadoConfig, id: string) =>
  (config.blocks ?? []).find((b) => b.id === id)?.frame as
    | { x: number; y: number; w: number; h: number }
    | undefined;

const zOf = (config: ComunicadoConfig, id: string) =>
  (config.blocks ?? []).find((b) => b.id === id)?.style?.zIndex;

async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("alignSelected — projeção visual local (025)", () => {
  beforeEach(() => {
    mutationsMock.mockReset();
  });

  it("pinta ANTES do ACK e persiste via upsert_block do resultado projetado", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1", "c1"];

    act(() => {
      result.current.blocks.alignSelected("align-left");
    });

    // Palco projetado IMEDIATAMENTE — ack ainda pendente.
    expect(frameOf(result.current.configRef.current, "a1")?.x).toBe(10);
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(10);
    expect(frameOf(result.current.configRef.current, "c1")?.x).toBe(10);
    expect(result.current.history.canUndo).toBe(true);

    expect(server.deferred).toHaveLength(1);
    const ops = server.deferred[0]!.ops;
    expect(ops.every((op) => op.op === "upsert_block")).toBe(true);
    // Nenhum op align_blocks — a persistência carrega a geometria projetada.
    expect(ops.some((op) => op.op === "align_blocks")).toBe(false);

    await act(async () => {
      server.deferred[0]!.resolve(server.applyOps(ops));
    });
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(10);
  });

  it("025-R1: ack normalizado não cria segundo Undo — uma ação lógica", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.immediate);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1"];

    act(() => {
      result.current.blocks.alignSelected("align-top");
    });
    await flush();
    expect(frameOf(result.current.configRef.current, "b1")?.y).toBe(10);

    // O canônico materializa defaults de estilo (fingerprint difere da
    // projeção esparsa) — applyServerConfig aplica sem nova entrada de Undo.
    act(() => {
      result.current.history.undo();
    });
    expect(frameOf(result.current.configRef.current, "b1")?.y).toBe(40);
    // Exatamente uma ação lógica: pilha esgotada após um único undo.
    expect(result.current.history.canUndo).toBe(false);
  });

  it("025-R1: ack com ajuste semântico do backend aplica sem Undo extra", async () => {
    const config = twoBlockConfig();
    const server = makeFakeMutationServer(config);
    mutationsMock.mockImplementation(
      vi.fn((_p: string, _s: string, ops: MutationOps) => {
        const out = server.applyOps(ops);
        // Backend "clamp" autoritativo: normaliza x para 8.
        for (const b of (out.nativeConfig as { blocks: Array<{ frame: { x: number } }> }).blocks) {
          b.frame.x = 8;
        }
        return Promise.resolve(out);
      }),
    );
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config,
    });
    selectedIdsRef.current = ["a1", "b1"];

    act(() => {
      result.current.blocks.alignSelected("align-left");
    });
    await flush();
    // Ajuste semântico do backend é autoridade: aplica no palco (x=8).
    expect(frameOf(result.current.configRef.current, "a1")?.x).toBe(8);

    act(() => {
      result.current.history.undo();
    });
    // Um Undo volta ao estado pré-comando (x=10) — a correção do backend
    // pertence à mesma ação lógica.
    expect(frameOf(result.current.configRef.current, "a1")?.x).toBe(10);
  });

  it("distribute-h com 3 blocos projeta espaçamento imediato", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1", "c1"];

    act(() => {
      result.current.blocks.alignSelected("distribute-h");
    });
    // span=100, totalW=90 → gap=5 → b1.x=45
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(45);
    expect(server.deferred).toHaveLength(1);
  });

  it("no-op (distribute com <3) não projeta nem commita", () => {
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1"];
    act(() => {
      result.current.blocks.alignSelected("distribute-h");
    });
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(50);
    expect(mutationsMock).not.toHaveBeenCalled();
  });

  it("ACK atrasado em sequência A→B: geração B vence, ack stale não reverte", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1", "c1"];

    act(() => {
      result.current.blocks.alignSelected("align-left");
      result.current.blocks.alignSelected("align-top");
    });
    expect(server.deferred).toHaveLength(2);
    // B já está pintado: left+top → todos em x=10, y=10.
    expect(frameOf(result.current.configRef.current, "a1")).toEqual(
      expect.objectContaining({ x: 10, y: 10 }),
    );
    expect(frameOf(result.current.configRef.current, "c1")).toEqual(
      expect.objectContaining({ x: 10, y: 10 }),
    );

    await act(async () => {
      server.deferred[1]!.resolve(server.applyOps(server.deferred[1]!.ops));
    });
    expect(frameOf(result.current.configRef.current, "c1")?.y).toBe(10);

    await act(async () => {
      server.deferred[0]!.resolve(server.applyOps(server.deferred[0]!.ops));
    });
    // Ack de A (só left: y original 10/40/70) é geração stale — não reverte B.
    expect(frameOf(result.current.configRef.current, "b1")?.y).toBe(10);
    expect(frameOf(result.current.configRef.current, "c1")?.y).toBe(10);
  });

  it("falha não-CAS: projeção permanece (autosave/conflict machinery decide)", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1", "b1", "c1"];

    act(() => {
      result.current.blocks.alignSelected("align-left");
    });
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(10);

    await act(async () => {
      server.deferred[0]!.reject(new Error("network timeout"));
    });
    // Não reverte para o estado anterior — a recuperação é do autosave/409.
    expect(frameOf(result.current.configRef.current, "b1")?.x).toBe(10);
  });
});

describe("z-order — projeção visual local (025)", () => {
  beforeEach(() => {
    mutationsMock.mockReset();
  });

  it("bringToFront pinta antes do ACK e persiste zIndex projetado via upsert", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1"];

    act(() => {
      result.current.blocks.bringToFront();
    });
    // Reindex: [b1=1, c1=2, a1=3]
    expect(zOf(result.current.configRef.current, "a1")).toBe(3);
    expect(zOf(result.current.configRef.current, "b1")).toBe(1);

    const ops = server.deferred[0]!.ops;
    expect(ops.every((op) => op.op === "upsert_block")).toBe(true);
    expect(ops.some((op) => op.op === "reorder_block_z")).toBe(false);
    const upsertedIds = ops
      .map((op) => (op.block as { id: string }).id)
      .sort();
    // a1 mudou de z — somente os blocos com zIndex alterado entram no ack.
    expect(upsertedIds).toContain("a1");
  });

  it("undo após projeção de camada restaura ordem anterior", async () => {
    const server = makeFakeMutationServer(twoBlockConfig());
    mutationsMock.mockImplementation(server.immediate);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: twoBlockConfig(),
    });
    selectedIdsRef.current = ["a1"];

    act(() => {
      result.current.blocks.bringToFront();
    });
    await flush();
    act(() => {
      result.current.history.undo();
    });
    // 025-R1: uma ação lógica = um Undo, mesmo com zIndex reindexado no ack.
    expect(zOf(result.current.configRef.current, "a1")).toBe(1);
  });
});
