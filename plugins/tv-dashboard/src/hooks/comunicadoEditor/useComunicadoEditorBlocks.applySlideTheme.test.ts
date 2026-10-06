import { act, renderHook } from "@testing-library/react";
import { useCallback, useRef } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

vi.mock("../../api/tvDashboardApi", async (importOriginal) => {
  const mod = await importOriginal<typeof import("../../api/tvDashboardApi")>();
  return { ...mod, applyPresentationMutations: vi.fn() };
});

import { applyPresentationMutations } from "../../api/tvDashboardApi";
import { COMUNICADO_SLIDE_THEMES } from "../../content/comunicadoSlideThemes";
import { useComunicadoEditorBlocks } from "./useComunicadoEditorBlocks";
import { snapshotConfig, useComunicadoEditorHistory } from "./useComunicadoEditorHistory";

/**
 * TV-THEME-PERSISTENCE-RACE-001 — aplicar tema em slide com blocos não pode
 * dividir a mudança em autosave full-config + mutation block-only: o ack
 * parcial reaplicava background/brandThemeKey antigos ("pisca e volta").
 * A aplicação agora é UMA PresentationMutation compound
 * (patch_native_config + upsert_block dos blocos restilizados).
 */

type MutationOps = Array<{ op: string; [key: string]: unknown }>;

const mutationsMock = vi.mocked(applyPresentationMutations);

/** Mini fake do backend: aplica ops sobre o estado persistido e devolve o canonical. */
function makeFakeMutationServer(initial: ComunicadoConfig) {
  let persisted = JSON.parse(JSON.stringify(initial)) as Record<string, unknown>;
  const deferred: Array<{
    ops: MutationOps;
    resolve: (result: { nativeConfig: Record<string, unknown> }) => void;
  }> = [];

  const applyOps = (ops: MutationOps) => {
    const cfg = JSON.parse(JSON.stringify(persisted)) as Record<string, unknown> & {
      blocks?: Array<Record<string, unknown>>;
    };
    for (const op of ops) {
      if (op.op === "patch_native_config") {
        for (const [key, value] of Object.entries(
          (op.patch as Record<string, unknown>) ?? {},
        )) {
          if (value === null) delete cfg[key];
          else cfg[key] = value;
        }
      } else if (op.op === "upsert_block") {
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
    /** Resposta imediata: aplica ops ao estado persistido e devolve o ack. */
    immediate: vi.fn((_p: string, _s: string, ops: MutationOps) =>
      Promise.resolve(applyOps(ops)),
    ),
    /** Resposta controlada: captura para resolver fora de ordem (race). */
    controlled: vi.fn(
      (_p: string, _s: string, ops: MutationOps) =>
        new Promise<{ nativeConfig: Record<string, unknown> }>((resolve) => {
          deferred.push({ ops, resolve });
        }),
    ),
  };
}

function populatedConfig(): ComunicadoConfig {
  return {
    version: 2,
    background: { type: "color", value: "#ffffff" },
    brandThemeKey: "delpi-light",
    blocks: [
      {
        id: "h1",
        type: "heading",
        content: "Título",
        contentRuns: [{ text: "Título" }],
        frame: { x: 10, y: 10, w: 400, h: 60 },
        style: { color: "#1f2937" },
      },
      {
        id: "t1",
        type: "text",
        content: "Corpo",
        contentRuns: [{ text: "Corpo" }],
        frame: { x: 10, y: 90, w: 400, h: 40 },
        style: { color: "#1f2937" },
      },
      {
        id: "s1",
        type: "shape",
        shape: "rectangle",
        frame: { x: 10, y: 150, w: 120, h: 60 },
        style: { fill: "#e5e7eb", stroke: "#9ca3af", color: "#1f2937" },
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
  const applyConfigCalls: Array<{ persist: boolean }> = [];
  const selectedIdsRef = { current: [] as string[] };
  const hook = renderHook(() => {
    const configRef = useRef<ComunicadoConfig>(args.config);
    const removeSelectedRef = useRef(() => {});
    const updateBlockTextFieldsRef = useRef(() => {});
    const applyConfig = useCallback(
      (next: ComunicadoConfig, options?: { persist?: boolean }) => {
        applyConfigCalls.push({ persist: options?.persist !== false });
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
  return { ...hook, persistedPayloads, applyConfigCalls, selectedIdsRef };
}

const darkTheme = () => COMUNICADO_SLIDE_THEMES.find((t) => t.key === "delpi-dark")!;
const midnightTheme = () =>
  COMUNICADO_SLIDE_THEMES.find((t) => t.key === "midnight")!;

async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

describe("applySlideTheme — TV-THEME-PERSISTENCE-RACE-001", () => {
  beforeEach(() => {
    mutationsMock.mockReset();
  });

  it("slide com blocos: UM mutation compound; ack não reverte nem reenfileira tema antigo", async () => {
    const server = makeFakeMutationServer(populatedConfig());
    mutationsMock.mockImplementation(server.immediate);
    const { result, persistedPayloads } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: populatedConfig(),
    });

    act(() => {
      result.current.blocks.applySlideTheme(darkTheme());
    });
    // Preview otimista instantâneo.
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-dark");

    await flush();

    // Uma única PresentationMutation carrega slide-level + blocks.
    expect(mutationsMock).toHaveBeenCalledTimes(1);
    const ops = mutationsMock.mock.calls[0]![2] as MutationOps;
    const patch = ops.find((op) => op.op === "patch_native_config");
    expect(patch).toBeTruthy();
    expect((patch!.patch as Record<string, unknown>).brandThemeKey).toBe(
      "delpi-dark",
    );
    expect((patch!.patch as Record<string, unknown>).background).toEqual(
      darkTheme().background,
    );
    const upserts = ops.filter((op) => op.op === "upsert_block");
    expect(
      upserts
        .map((op) => (op.block as { id: string }).id)
        .sort(),
    ).toEqual(["h1", "s1", "t1"]);
    // Sem ghost-create: ids existentes, sem createIfMissing.
    for (const op of upserts) expect(op.createIfMissing).toBeUndefined();

    // Canonical ack manteve o tema — nada voltou para o estado anterior.
    const final = result.current.configRef.current;
    expect(final.background).toEqual(darkTheme().background);
    expect(final.brandThemeKey).toBe("delpi-dark");
    const heading = (final.blocks ?? []).find((b) => b.id === "h1");
    expect(heading?.style?.color).toBe(darkTheme().textColor);
    const shape = (final.blocks ?? []).find((b) => b.id === "s1");
    expect(shape?.style?.fill).toBe(darkTheme().accent);

    // Nenhum autosave enfileirado carrega o tema anterior (snapshot
    // normaliza gradientes — compara contra a forma persistida).
    const persistedDarkBg = snapshotConfig({
      version: 2,
      background: darkTheme().background,
      blocks: [],
    }).background;
    expect(persistedPayloads.length).toBeGreaterThan(0);
    for (const payload of persistedPayloads) {
      expect(payload.brandThemeKey ?? "").not.toBe("delpi-light");
      expect(payload.background).toEqual(persistedDarkBg);
    }
  });

  it("slide vazio: só patch_native_config e continua funcionando", async () => {
    const empty: ComunicadoConfig = {
      version: 2,
      background: { type: "color", value: "#ffffff" },
      blocks: [],
    };
    const server = makeFakeMutationServer(empty);
    mutationsMock.mockImplementation(server.immediate);
    const { result } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: empty,
    });

    act(() => {
      result.current.blocks.applySlideTheme(darkTheme());
    });
    await flush();

    expect(mutationsMock).toHaveBeenCalledTimes(1);
    const ops = mutationsMock.mock.calls[0]![2] as MutationOps;
    expect(ops.map((op) => op.op)).toEqual(["patch_native_config"]);
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-dark");
    expect(result.current.configRef.current.background).toEqual(
      darkTheme().background,
    );
  });

  it("tema não-Delpi limpa brandThemeKey via patch (contrato \"\")", async () => {
    const withBrand = populatedConfig();
    withBrand.brandThemeKey = "delpi-dark";
    withBrand.background = darkTheme().background;
    const server = makeFakeMutationServer(withBrand);
    mutationsMock.mockImplementation(server.immediate);
    const { result } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: withBrand,
    });

    act(() => {
      result.current.blocks.applySlideTheme(midnightTheme());
    });
    await flush();

    const ops = mutationsMock.mock.calls[0]![2] as MutationOps;
    const patch = ops.find((op) => op.op === "patch_native_config");
    expect((patch!.patch as Record<string, unknown>).brandThemeKey).toBe("");
    expect((patch!.patch as Record<string, unknown>).background).toEqual(
      midnightTheme().background,
    );
    // Sem marca semanticamente ("" ou ausente) — nunca delpi-dark.
    expect(
      result.current.configRef.current.brandThemeKey ?? "",
    ).not.toBe("delpi-dark");
    expect(result.current.configRef.current.background).toEqual(
      midnightTheme().background,
    );
    const shape = (result.current.configRef.current.blocks ?? []).find(
      (b) => b.id === "s1",
    );
    expect(shape?.style?.stroke).toBe(midnightTheme().shapeStroke);
  });

  it("race A→B com ack fora de ordem: geração B vence, ack stale não reverte", async () => {
    const server = makeFakeMutationServer(populatedConfig());
    mutationsMock.mockImplementation(server.controlled);
    const { result, applyConfigCalls } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: populatedConfig(),
    });

    act(() => {
      result.current.blocks.applySlideTheme(darkTheme());
      result.current.blocks.applySlideTheme(midnightTheme());
    });
    expect(server.deferred).toHaveLength(2);

    // B (midnight) resolve primeiro e é aplicado.
    await act(async () => {
      server.deferred[1]!.resolve(server.applyOps(server.deferred[1]!.ops));
    });
    expect(result.current.configRef.current.background).toEqual(
      midnightTheme().background,
    );

    const callsBeforeStale = applyConfigCalls.length;
    // A (delpi-dark) resolve por último — ack stale não pode reverter B.
    await act(async () => {
      server.deferred[0]!.resolve(server.applyOps(server.deferred[0]!.ops));
    });
    expect(applyConfigCalls.length).toBe(callsBeforeStale);
    expect(result.current.configRef.current.background).toEqual(
      midnightTheme().background,
    );
    expect(result.current.configRef.current.brandThemeKey ?? "").toBe("");
  });

  it("negative: mutação de bloco não relacionada continua com ack canônico", async () => {
    const server = makeFakeMutationServer(populatedConfig());
    mutationsMock.mockImplementation(server.immediate);
    const { result, selectedIdsRef } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: populatedConfig(),
    });

    selectedIdsRef.current = ["h1"];
    act(() => {
      result.current.blocks.rotateSelected(15);
    });
    await flush();

    expect(mutationsMock).toHaveBeenCalledTimes(1);
    const ops = mutationsMock.mock.calls[0]![2] as MutationOps;
    expect(ops.every((op) => op.op === "upsert_block")).toBe(true);
    // Tema/background original preservado — nada de replay de config antiga.
    expect(result.current.configRef.current.background).toEqual({
      type: "color",
      value: "#ffffff",
    });
    const heading = (result.current.configRef.current.blocks ?? []).find(
      (b) => b.id === "h1",
    );
    expect(heading?.style?.rotation).toBe(15);
  });

  it("undo/redo: um passo lógico e sem replay assíncrono de tema", async () => {
    const server = makeFakeMutationServer(populatedConfig());
    mutationsMock.mockImplementation(server.immediate);
    const { result, applyConfigCalls } = renderEditor({
      playlistId: "pl1",
      slideId: "sl1",
      config: populatedConfig(),
    });

    act(() => {
      result.current.blocks.applySlideTheme(darkTheme());
    });
    await flush();
    expect(result.current.history.canUndo).toBe(true);
    const mutationsAfterApply = mutationsMock.mock.calls.length;

    act(() => {
      result.current.history.undo();
    });
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-light");
    expect(result.current.configRef.current.background).toEqual({
      type: "color",
      value: "#ffffff",
    });
    expect(result.current.history.canRedo).toBe(true);

    await flush();
    // Undo não dispara mutation nem replay assíncrono posterior.
    expect(mutationsMock.mock.calls.length).toBe(mutationsAfterApply);
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-light");

    act(() => {
      result.current.history.redo();
    });
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-dark");
    await flush();
    expect(mutationsMock.mock.calls.length).toBe(mutationsAfterApply);
    // Nenhum applyConfig posterior reintroduziu o estado pós-undo como
    // replay assíncrono — o último apply foi o redo explícito.
    const last = applyConfigCalls[applyConfigCalls.length - 1];
    expect(last?.persist).toBe(true);
  });

  it("sem playlist/slide (modo local): tema aplica só no histórico", () => {
    const { result } = renderEditor({ config: populatedConfig() });
    act(() => {
      result.current.blocks.applySlideTheme(darkTheme());
    });
    expect(result.current.configRef.current.brandThemeKey).toBe("delpi-dark");
    expect(mutationsMock).not.toHaveBeenCalled();
    expect(result.current.history.canUndo).toBe(true);
  });
});
