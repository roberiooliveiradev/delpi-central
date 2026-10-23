import { describe, expect, it } from "vitest";

import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import {
  coveredKeysForBlocks,
  coveredKeysForMutationOps,
  createPendingProjectionRegistry,
  diffedFieldKeys,
  driftedPendingKeys,
  pendingBlockKey,
  pendingFieldKey,
  resolvePersistableConfig,
} from "./pendingMutationProjection";

function cfg(partial: Partial<ComunicadoConfig>): ComunicadoConfig {
  return { version: 4, ...partial };
}

const blockA = { id: "a", type: "text", content: "A", frame: { x: 40, y: 10, w: 20, h: 10 } };
const blockB = { id: "b", type: "text", content: "B", frame: { x: 60, y: 10, w: 20, h: 10 } };

describe("pendingMutationProjection registry", () => {
  it("marca entidade com baseline e libera no settle da geração", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [blockA as never] });
    reg.mark([pendingBlockKey("a")], baseline, 1);
    expect(reg.hasPending()).toBe(true);
    reg.settle([pendingBlockKey("a")], 1);
    expect(reg.hasPending()).toBe(false);
  });

  it("sem baseline disponível não marca (fail-open)", () => {
    const reg = createPendingProjectionRegistry();
    reg.mark([pendingBlockKey("a")], undefined, 1);
    expect(reg.hasPending()).toBe(false);
  });

  it("primeiro baseline vence e gerações coexistem até todas fazerem settle", () => {
    const reg = createPendingProjectionRegistry();
    const b0 = cfg({ blocks: [{ ...blockA, frame: { x: 40, y: 0, w: 1, h: 1 } } as never] });
    const b1 = cfg({ blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never] });
    reg.mark([pendingBlockKey("a")], b0, 1);
    reg.mark([pendingBlockKey("a")], b1, 2); // baseline b0 preservado
    reg.settle([pendingBlockKey("a")], 1, b1); // promove baseline ao confirmado
    const entry = reg.get(pendingBlockKey("a"));
    expect((entry?.baseline as typeof blockA).frame.x).toBe(8);
    reg.settle([pendingBlockKey("a")], 2);
    expect(reg.hasPending()).toBe(false);
  });
});

describe("resolvePersistableConfig", () => {
  it("substitui bloco pendente pelo baseline confirmado", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [blockA as never] });
    reg.mark([pendingBlockKey("a")], baseline, 1);
    const live = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never, blockB as never],
    });
    const { resolved, dropped } = resolvePersistableConfig(live, reg);
    expect(dropped).toBe(true);
    expect(resolved.blocks?.find((b) => b.id === "a")?.frame.x).toBe(40);
    expect(resolved.blocks?.find((b) => b.id === "b")).toEqual(blockB);
  });

  it("omite inserção pendente (ausente no baseline)", () => {
    const reg = createPendingProjectionRegistry();
    reg.mark([pendingBlockKey("novo")], cfg({ blocks: [blockA as never] }), 1);
    const live = cfg({ blocks: [blockA as never, { ...blockB, id: "novo" } as never] });
    const { resolved } = resolvePersistableConfig(live, reg);
    expect(resolved.blocks?.map((b) => b.id)).toEqual(["a"]);
  });

  it("restaura campo top-level pendente e preserva edições autosave-only", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ background: { type: "color", value: "#111" } as never });
    reg.mark([pendingFieldKey("background")], baseline, 1);
    const live = cfg({
      background: { type: "color", value: "#fff" } as never,
      dataFilters: { filial: "01" } as never,
    });
    const { resolved } = resolvePersistableConfig(live, reg);
    expect((resolved.background as { value: string }).value).toBe("#111");
    expect(resolved.dataFilters).toEqual({ filial: "01" });
  });

  it("registry vazio retorna o config inalterado", () => {
    const reg = createPendingProjectionRegistry();
    const live = cfg({ blocks: [blockA as never] });
    const { resolved, dropped } = resolvePersistableConfig(live, reg);
    expect(dropped).toBe(false);
    expect(resolved).toBe(live);
  });
});

describe("coveredKeysForMutationOps", () => {
  it("deriva chaves de blockId/blockIds/block.id", () => {
    const keys = coveredKeysForMutationOps([
      { op: "upsert_block", block: { id: "x" } },
      { op: "transform_text_case", blockId: "y" },
      { op: "align_blocks", blockIds: ["p", "q"] },
    ]);
    expect(keys).toEqual(
      expect.arrayContaining(["block:x", "block:y", "block:p", "block:q"]),
    );
  });

  it("deriva chaves de patch_native_config e data models", () => {
    const keys = coveredKeysForMutationOps([
      { op: "patch_native_config", patch: { background: {}, brandThemeKey: "delpi-dark" } },
      { op: "delete_data_model", modelId: "m1" },
      { op: "upsert_data_model", model: { id: "m2" } },
    ]);
    expect(keys).toEqual(
      expect.arrayContaining([
        "field:background",
        "field:brandThemeKey",
        "dataModel:m1",
        "dataModel:m2",
      ]),
    );
  });
});

describe("driftedPendingKeys (undo/redo sobre mutation pendente)", () => {
  it("detecta entidade cujo live diverge da projeção registrada", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [{ ...blockA } as never] });
    const projected = {
      ...blockA,
      frame: { x: 8, y: 10, w: 20, h: 10 },
    };
    const liveProjected = cfg({ blocks: [projected as never] });
    reg.mark([pendingBlockKey("a")], baseline, 1, liveProjected);

    // Live ainda no valor projetado → sem drift.
    expect(driftedPendingKeys(reg, liveProjected)).toEqual([]);

    // Undo restaurou o valor pré-projeção → drift pede write compensatório.
    expect(driftedPendingKeys(reg, baseline)).toEqual(["block:a"]);
  });

  it("drift em campo top-level (patch_native_config) é detectado", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ background: "white" } as never);
    const liveProjected = cfg({ background: "#123456" } as never);
    reg.mark([pendingFieldKey("background")], baseline, 1, liveProjected);
    expect(driftedPendingKeys(reg, cfg({ background: "white" } as never))).toEqual(
      ["field:background"],
    );
    expect(driftedPendingKeys(reg, liveProjected)).toEqual([]);
  });

  it("undo de inserção pendente (bloco some do live) gera drift", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [] });
    const liveProjected = cfg({ blocks: [blockB as never] });
    reg.mark([pendingBlockKey("b")], baseline, 1, liveProjected);
    expect(driftedPendingKeys(reg, cfg({ blocks: [] }))).toEqual(["block:b"]);
  });
});

describe("diffedFieldKeys / coveredKeysForBlocks", () => {
  it("detecta campos projetados fora dos ops (ex.: groupTransforms)", () => {
    const sharedFilters = { f: "1" };
    const baseline = cfg({ blocks: [blockA as never], dataFilters: sharedFilters as never });
    const live = cfg({
      blocks: [blockA as never],
      dataFilters: sharedFilters as never,
      groupTransforms: { g1: { rotation: 15 } } as never,
      version: 5,
    });
    expect(diffedFieldKeys(baseline, live)).toEqual(["field:groupTransforms"]);
  });

  it("coveredKeysForBlocks lista ids", () => {
    expect(coveredKeysForBlocks([{ id: "a" }, { id: "b" }, {}])).toEqual([
      "block:a",
      "block:b",
    ]);
  });
});
