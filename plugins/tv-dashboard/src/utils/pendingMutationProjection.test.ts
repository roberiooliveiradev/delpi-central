import { describe, expect, it } from "vitest";

import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import {
  coveredKeysForBlocks,
  coveredKeysForMutationOps,
  createPendingProjectionRegistry,
  diffedFieldKeys,
  driftedPendingKeys,
  mergeAutosaveOnlyOverlay,
  pendingBlockKey,
  pendingFieldKey,
  resolvePersistableConfig,
  resolvePersistableDispatchDecision,
  resolveProjectionBaseline,
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

  it("baseline autoritativo cobre a janela de stash vazio (028)", () => {
    const reg = createPendingProjectionRegistry();
    const authoritative = cfg({ blocks: [blockA as never] });
    const baseline = resolveProjectionBaseline(undefined, authoritative);
    reg.mark([pendingBlockKey("a")], baseline, 1);
    expect(reg.hasPending()).toBe(true);
    // A serialização persistível usa o estado confirmado, não a projeção.
    const live = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    const { resolved } = resolvePersistableConfig(live, reg);
    const resolvedA = (resolved.blocks ?? []).find((b) => b.id === "a") as
      | typeof blockA
      | undefined;
    expect(resolvedA?.frame.x).toBe(40);
  });

  it("stash vence sobre o autoritativo quando presente (028)", () => {
    const stash = cfg({ blocks: [{ ...blockA, content: "stash" } as never] });
    const authoritative = cfg({ blocks: [{ ...blockA, content: "auth" } as never] });
    const baseline = resolveProjectionBaseline(stash, authoritative);
    expect((baseline?.blocks?.[0] as typeof blockA).content).toBe("stash");
  });

  it("sem stash e sem autoritativo permanece undefined (fail-open)", () => {
    expect(resolveProjectionBaseline(undefined, null)).toBeUndefined();
    expect(resolveProjectionBaseline(undefined, undefined)).toBeUndefined();
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

describe("mergeAutosaveOnlyOverlay (028 — cenário misto)", () => {
  const covered = new Set([pendingBlockKey("a")]);

  it("retorna null quando live e canônico coincidem", () => {
    const c = cfg({ blocks: [blockA as never] });
    expect(mergeAutosaveOnlyOverlay(c, c, covered)).toBeNull();
    expect(mergeAutosaveOnlyOverlay(undefined, c, covered)).toBeNull();
  });

  it("preserva edição autosave-only em bloco não-coberto por cima do canônico", () => {
    const canonical = cfg({
      blocks: [
        { ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never,
        blockB as never,
      ],
    });
    const live = cfg({
      blocks: [
        { ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never,
        { ...blockB, content: "texto digitado" } as never,
      ],
    });
    const merged = mergeAutosaveOnlyOverlay(live, canonical, covered);
    expect(merged).not.toBeNull();
    const blocks = (merged as ComunicadoConfig).blocks ?? [];
    expect((blocks.find((b) => b.id === "a") as typeof blockA).frame.x).toBe(8);
    expect((blocks.find((b) => b.id === "b") as typeof blockB).content).toBe(
      "texto digitado",
    );
  });

  it("não reintroduz bloco presente só no live (delete confirmado vence)", () => {
    const canonical = cfg({ blocks: [blockA as never] });
    const live = cfg({ blocks: [blockA as never, blockB as never] });
    const merged = mergeAutosaveOnlyOverlay(live, canonical, new Set());
    expect(merged).toBeNull();
  });

  it("entidade coberta segue o canônico mesmo com live divergente", () => {
    const canonical = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    const live = cfg({
      blocks: [{ ...blockA, frame: { x: 99, y: 0, w: 1, h: 1 } } as never],
    });
    const merged = mergeAutosaveOnlyOverlay(live, canonical, covered);
    expect(merged).toBeNull();
  });

  it("campo top-level não-coberto usa live; coberto usa canônico", () => {
    const canonical = cfg({
      headline: "h-srv",
      speakerNotes: "nota-srv",
    } as Partial<ComunicadoConfig>);
    const live = cfg({
      headline: "h-srv",
      speakerNotes: "nota-digitada",
    } as Partial<ComunicadoConfig>);
    const merged = mergeAutosaveOnlyOverlay(
      live,
      canonical,
      new Set([pendingFieldKey("headline")]),
    );
    expect(merged).not.toBeNull();
    const rec = merged as unknown as Record<string, unknown>;
    expect(rec.headline).toBe("h-srv");
    expect(rec.speakerNotes).toBe("nota-digitada");
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

describe("resolvePersistableDispatchDecision (028 — guarda de dispatch)", () => {
  const serialize = (c: ComunicadoConfig) =>
    JSON.parse(JSON.stringify(c)) as Record<string, unknown>;

  it("slide corrente: captura igual à visão persistível atual → send (mutation rejeitada, baseline segue válido)", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [blockA as never] });
    const live = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    reg.mark([pendingBlockKey("a")], baseline, 1); // mutation falhou → marks ficam
    const { resolved } = resolvePersistableConfig(live, reg);
    const captured = serialize(resolved);
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: true,
        live,
        registry: reg,
        serialize,
      }),
    ).toEqual({ send: true });
  });

  it("slide corrente: captura com baseline coberto após commit → skip (não reverte projeção confirmada)", () => {
    const reg = createPendingProjectionRegistry();
    const baseline = cfg({ blocks: [blockA as never] });
    reg.mark([pendingBlockKey("a")], baseline, 1);
    const captured = serialize(baseline); // payload {a@40} capturado pré-commit
    const canonical = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    reg.settle([pendingBlockKey("a")], 1, canonical); // commit + applyAck
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: true,
        live: canonical,
        registry: reg,
        serialize,
      }),
    ).toEqual({ send: false });
  });

  it("slide corrente: captura igual ao resolvido mas já persistida → skip (no-op write que só bumpa revisão)", () => {
    const reg = createPendingProjectionRegistry();
    const canonical = cfg({ blocks: [blockA as never] });
    const captured = serialize(canonical);
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: true,
        live: canonical,
        registry: reg,
        authoritativeKey: JSON.stringify(captured),
        serialize,
      }),
    ).toEqual({ send: false });
  });

  it("slide corrente: commit registrado antes do applyAck (janela settle→ACK) → skip no-op write", () => {
    const reg = createPendingProjectionRegistry();
    const canonical = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    /* PATCH despacha no hop entre settle e applyAck: registry vazio,
     * live já é o canônico, mas authoritativePersistableRef ainda é o estado
     * pré-commit — o registro de commit do hop mais cedo suprime o no-op. */
    const captured = serialize(canonical);
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: true,
        live: canonical,
        registry: reg,
        authoritativeKey: JSON.stringify(serialize(cfg({ blocks: [blockA as never] }))),
        committed: { canonical, coveredKeys: new Set([pendingBlockKey("a")]) },
        serialize,
      }),
    ).toEqual({ send: false });
  });

  it("slide corrente: captura correta com delta ainda não persistido → send", () => {
    const reg = createPendingProjectionRegistry();
    const live = cfg({ blocks: [blockA as never] });
    const captured = serialize(live);
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: true,
        live,
        registry: reg,
        authoritativeKey: JSON.stringify(serialize(cfg({ blocks: [blockB as never] }))),
        serialize,
      }),
    ).toEqual({ send: true });
  });

  it("slide não-corrente sem commit registrado → send (flush de navegação com mutation rejeitada)", () => {
    const reg = createPendingProjectionRegistry();
    const captured = serialize(cfg({ blocks: [blockA as never] }));
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: false,
        live: undefined,
        registry: reg,
        committed: null,
        serialize,
      }),
    ).toEqual({ send: true });
  });

  it("slide não-corrente pós-commit sem delta autosave → skip", () => {
    const reg = createPendingProjectionRegistry();
    const canonical = cfg({
      blocks: [{ ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never],
    });
    const captured = serialize(cfg({ blocks: [blockA as never] })); // baseline {a@40}
    expect(
      resolvePersistableDispatchDecision({
        captured,
        isCurrentSlide: false,
        live: undefined,
        registry: reg,
        committed: {
          canonical,
          coveredKeys: new Set([pendingBlockKey("a")]),
        },
        serialize,
      }),
    ).toEqual({ send: false });
  });

  it("slide não-corrente pós-commit com delta autosave-only → reEmit canônico+delta", () => {
    const reg = createPendingProjectionRegistry();
    const canonical = cfg({
      blocks: [
        { ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never,
        blockB as never,
      ],
    });
    // Captura pré-commit: baseline no bloco coberto + edição digitada no não-coberto.
    const captured = serialize(
      cfg({
        blocks: [
          blockA as never,
          { ...blockB, content: "texto digitado" } as never,
        ],
      }),
    );
    const decision = resolvePersistableDispatchDecision({
      captured,
      isCurrentSlide: false,
      live: undefined,
      registry: reg,
      committed: { canonical, coveredKeys: new Set([pendingBlockKey("a")]) },
      serialize,
    });
    expect(decision.send).toBe(false);
    const blocks = (decision.reEmit?.blocks ?? []) as typeof blockA[];
    expect(blocks.find((b) => b.id === "a")?.frame.x).toBe(8);
    expect(blocks.find((b) => b.id === "b")?.content).toBe("texto digitado");
  });

  it("slide não-corrente: captura já igual ao merged → send (dispatch do save reemitido)", () => {
    const reg = createPendingProjectionRegistry();
    const canonical = cfg({
      blocks: [
        { ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never,
        blockB as never,
      ],
    });
    const merged = serialize(
      cfg({
        blocks: [
          { ...blockA, frame: { x: 8, y: 0, w: 1, h: 1 } } as never,
          { ...blockB, content: "texto digitado" } as never,
        ],
      }),
    );
    expect(
      resolvePersistableDispatchDecision({
        captured: merged,
        isCurrentSlide: false,
        live: undefined,
        registry: reg,
        committed: { canonical, coveredKeys: new Set([pendingBlockKey("a")]) },
        serialize,
      }),
    ).toEqual({ send: true });
  });
});
