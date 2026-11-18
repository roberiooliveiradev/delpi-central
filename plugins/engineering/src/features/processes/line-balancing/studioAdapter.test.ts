/** Adaptador roteiro oficial → Studio: unidade (min→s uma vez),
 * identidade por `op.key`, tempos ausentes UNKNOWN, setup separado do
 * tempo peça, truncamento propagado, migração legada e parâmetros M1. */

import { beforeEach, describe, expect, it, vi } from "vitest";
import type { RoutingStageView } from "../../products/routing/routingGrouping";
import {
  buildManualStudyInput,
  buildObservedStudyInput,
  buildStudioExportPayload,
  deriveBalanceParams,
  loadStudioDraft,
  migrateLegacyDraft,
  saveStudioDraft,
  studioDraftContext,
  studioDraftKey,
} from "./studioAdapter";

const stage: RoutingStageView = {
  key: "90264302#0",
  product_code: "90264302",
  bom_level: 0,
  branch: "01",
  route_code: "01",
  operations: [
    {
      key: "90264302#0#010#CT1#R1",
      operation_code: "010",
      operation_description: "Corte",
      work_center: "CT1",
      resource_code: "R1",
      operation_type: null,
      mandatory_operation: null,
      mandatory_sequence: null,
      mandatory_report: null,
      time_minutes_piece: 2.5,
      setup_hours: 0.5,
      components: [{ code: "C1", description: null, sequence: null }],
      source_rows: 3,
    },
    {
      key: "90264302#0#020#CT2#R2",
      operation_code: "020",
      operation_description: null,
      work_center: "CT2",
      resource_code: "R2",
      operation_type: null,
      mandatory_operation: null,
      mandatory_sequence: null,
      mandatory_report: null,
      time_minutes_piece: null,
      setup_hours: null,
      components: [],
      source_rows: 1,
    },
  ],
};

describe("buildObservedStudyInput", () => {
  it("converte min/peça para s/peça uma única vez e preserva identidade", () => {
    const input = buildObservedStudyInput({ stage, productCode: "90264302", branch: "01", truncated: true });
    expect(input.source).toBe("OBSERVED_ROUTING");
    expect(input.operations[0].id).toBe(stage.operations[0].key);
    expect(input.operations[0].durationSeconds).toBe(150);
    expect(input.operations[0].name).toBe("Corte");
    expect(input.routing.truncated).toBe(true);
    expect(input.routing.stageId).toBe(stage.key);
  });

  it("tempo ausente vira null (UNKNOWN), nunca zero; setup fora do tempo peça", () => {
    const input = buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" });
    expect(input.operations[1].durationSeconds).toBeNull();
    expect(input.operations[0].reference).toContain("Setup 0.5 h/lote");
    expect(input.operations[0].durationSeconds).toBe(150);
    expect(input.operations[1].reference).toBe("OP 020 · CT CT2 · R2");
  });

  it("dedup preservado — uma operação por identidade oficial (op.key)", () => {
    const input = buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" });
    expect(input.operations).toHaveLength(2);
    expect(new Set(input.operations.map((o) => o.id)).size).toBe(2);
  });
});

describe("rascunho sessionStorage", () => {
  beforeEach(() => {
    const map = new Map<string, string>();
    vi.stubGlobal("sessionStorage", {
      getItem: (k: string) => map.get(k) ?? null,
      setItem: (k: string, v: string) => void map.set(k, v),
      removeItem: (k: string) => void map.delete(k),
      clear: () => map.clear(),
    });
  });

  it("salva, restaura e detecta stale por fingerprint", () => {
    const ctx = studioDraftContext({ productCode: "90264302", branch: "01", stage });
    const key = studioDraftKey("user-1", ctx);
    const seed = buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" });
    expect(saveStudioDraft(key, ctx, seed)).toBe("saved");
    expect(loadStudioDraft(key, ctx).status).toBe("ok");
    const stale = loadStudioDraft(key, { ...ctx, sourceFingerprint: "deadbeef" });
    expect(stale.status).toBe("stale");
    expect(loadStudioDraft(studioDraftKey("user-2", ctx), ctx).status).toBe("none");
  });
});

describe("migrateLegacyDraft", () => {
  it("converte postos legados em postos do Studio, descartando refs inexistentes", () => {
    const observed = buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" });
    const legacy = {
      schemaVersion: 2 as const,
      savedAt: "x",
      context: { productCode: "90264302", branch: "01", stageKey: stage.key, sourceFingerprint: "fp" },
      activeScenarioId: "s1",
      scenarios: [
        {
          clientId: "s1", label: "A", mode: "posts" as const,
          inputs: { demand: "", shiftMinutes: "", breakMinutes: "", batchSize: "", numStations: "" },
          posts: [
            {
              clientId: "post-1", name: "Posto 01",
              operationRefs: [stage.operations[0].key, "ghost-ref"],
              operators: null, parallelPositions: null, note: "",
            },
          ],
        },
      ],
    };
    const migrated = migrateLegacyDraft(legacy, observed);
    expect(migrated.source).toBe("OBSERVED_ROUTING");
    expect(migrated.stations).toEqual([{ id: "post-1", name: "Posto 01" }]);
    expect(migrated.scenarios[0].assignments).toEqual([
      { operationId: stage.operations[0].key, stationId: "post-1" },
    ]);
  });
});

describe("deriveBalanceParams", () => {
  const study = {
    ...buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" }),
    stations: [{ id: "p1", name: "Posto 01" }],
    conditions: {
      shift: { mode: "MINUTES" as const, durationMinutes: 480, breaks: [30] },
      demandUnitsPerShift: 100,
      batchUnits: 20,
    },
  };

  it("deriva vocabulário fechado do POST oficial", () => {
    const derived = deriveBalanceParams(study, "01");
    expect(derived.ok).toBe(true);
    if (derived.ok) {
      expect(derived.params.demand).toBe(100);
      expect(derived.params.available_minutes).toBe(450);
      expect(derived.params.batch_size).toBe(20);
      expect(derived.params.num_stations).toBe(1);
      expect(derived.params.branch).toBe("01");
    }
  });

  it("sem demanda positiva ou turno válido, recusa com issues", () => {
    const noDemand = deriveBalanceParams({ ...study, conditions: { ...study.conditions, demandUnitsPerShift: undefined } }, "01");
    expect(noDemand.ok).toBe(false);
    const badShift = deriveBalanceParams(
      { ...study, conditions: { shift: { mode: "MINUTES" as const, durationMinutes: 0, breaks: [] }, demandUnitsPerShift: 5 } },
      "01",
    );
    expect(badShift.ok).toBe(false);
    expect(deriveBalanceParams(buildManualStudyInput(), "01").ok).toBe(false);
  });
});

describe("buildStudioExportPayload", () => {
  it("marca SIMULATION/DRAFT_LOCAL e nunca inventa tempos", () => {
    const study = {
      ...buildObservedStudyInput({ stage, productCode: "90264302", branch: "01" }),
      stations: [{ id: "p1", name: "Posto 01" }],
      scenarios: [{ id: "sc", name: "Cenário A", assignments: [{ operationId: stage.operations[0].key, stationId: "p1" }] }],
    };
    const payload = buildStudioExportPayload({ productCode: "90264302", branch: "01", stageLabel: "Estágio 0", study });
    expect(payload.title).toContain("SIMULATION");
    expect(payload.title).toContain("DRAFT_LOCAL");
    const r0 = payload.rows[0] as Record<string, unknown>;
    const r1 = payload.rows[1] as Record<string, unknown>;
    expect(r0.posto).toBe("Posto 01");
    expect(r0.proveniencia).toBe("OBSERVED");
    expect(r1.posto).toBe("Sem posto");
    expect(r1.tempo_s).toBe("UNKNOWN");
    expect(r1.proveniencia).toBe("UNKNOWN");
    expect(r0.limitacao).toBeTruthy();
  });
});
