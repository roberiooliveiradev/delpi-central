/** Routing Study V2 — lógica pura do rascunho de sessão (contrato
 * routing-study-session-state-contract.md). Storage injetado: nenhum
 * teste toca o navegador real. */

import { describe, expect, it } from "vitest";

import {
  buildStorageKey,
  computeSourceFingerprint,
  emptyDraft,
  inputsFingerprint,
  loadDraft,
  newClientId,
  newScenarioDraft,
  parseDraft,
  removeDraft,
  saveDraft,
  STUDY_SCHEMA_VERSION,
  type RoutingStudyDraft,
  type StudyDraftContext,
} from "./routingStudyDraft";
import type { RoutingStageView } from "./routingGrouping";

const CTX: StudyDraftContext = {
  productCode: "90264302",
  branch: "01",
  stageKey: "90264302#0",
  sourceFingerprint: "abc123",
};

function makeStage(ops: Partial<RoutingStageView["operations"][number]>[]): RoutingStageView {
  return {
    key: "90264302#0",
    product_code: "90264302",
    bom_level: 0,
    stage_code: "0",
    branch: "01",
    route_code: "01",
    operations: ops.map((o, i) => ({
      key: `op-${i}`,
      operation_code: o.operation_code ?? `0${i + 1}`,
      operation_description: o.operation_description ?? `OP${i}`,
      work_center: o.work_center ?? "CT-01",
      resource_code: o.resource_code ?? "R1",
      setup_hours: 0,
      time_minutes_piece: o.time_minutes_piece ?? 1,
      operation_type: null,
      mandatory_operation: null,
      mandatory_sequence: null,
      mandatory_report: null,
      source_rows: 1,
      components: [],
    })),
  } as RoutingStageView;
}

function memoryStorage(): Storage {
  const map = new Map<string, string>();
  return {
    getItem: (k) => map.get(k) ?? null,
    setItem: (k, v) => void map.set(k, String(v)),
    removeItem: (k) => void map.delete(k),
    clear: () => map.clear(),
    key: (i) => [...map.keys()][i] ?? null,
    get length() {
      return map.size;
    },
  } as Storage;
}

describe("buildStorageKey", () => {
  it("isola por identidade, produto, filial e estágio", () => {
    const key = buildStorageKey("user-sub-1", CTX);
    expect(key).toContain("user-sub-1");
    expect(key).toContain("90264302");
    expect(key).toContain("01");
    expect(key).toContain("90264302#0");
    expect(buildStorageKey("user-sub-2", CTX)).not.toBe(key);
    expect(buildStorageKey("user-sub-1", { ...CTX, branch: "02" })).not.toBe(
      key,
    );
  });

  it("usa anonymous quando não há identidade e 'all' para todas filiais", () => {
    const key = buildStorageKey(null, { ...CTX, branch: "" });
    expect(key).toContain("anonymous");
    expect(key).toContain(":all:");
  });
});

describe("computeSourceFingerprint", () => {
  it("é estável para a mesma fonte e muda quando o roteiro muda", () => {
    const a = computeSourceFingerprint(makeStage([{}, {}]));
    expect(computeSourceFingerprint(makeStage([{}, {}]))).toBe(a);
    expect(
      computeSourceFingerprint(makeStage([{ time_minutes_piece: 9 }, {}])),
    ).not.toBe(a);
    expect(computeSourceFingerprint(makeStage([{}]))).not.toBe(a);
  });
});

describe("save/load/parse", () => {
  it("round-trip: salva e recupera rascunho válido do contexto", () => {
    const storage = memoryStorage();
    const draft = emptyDraft(CTX);
    draft.scenarios[0].inputs.demand = "500";
    draft.scenarios[0].posts.push({
      clientId: "post-1",
      name: "Posto 01",
      operationRefs: ["op-1"],
      operators: 2,
      parallelPositions: 1,
      note: "teste",
    });
    const key = buildStorageKey("u", CTX);
    expect(saveDraft(storage, key, draft)).toBe("saved");
    const parsed = parseDraft(loadDraft(storage, key), CTX);
    expect(parsed.ok).toBe(true);
    if (parsed.ok) {
      expect(parsed.draft.scenarios[0].inputs.demand).toBe("500");
      expect(parsed.draft.scenarios[0].posts[0].name).toBe("Posto 01");
      expect(parsed.draft.scenarios[0].posts[0].operationRefs).toEqual([
        "op-1",
      ]);
    }
  });

  it("rejeita JSON inválido sem quebrar", () => {
    expect(parseDraft("{oops", CTX)).toEqual({
      ok: false,
      reason: "invalid_json",
    });
    expect(parseDraft(null, CTX)).toEqual({
      ok: false,
      reason: "invalid_json",
    });
  });

  it("rejeita schema de versão anterior", () => {
    const old = { ...emptyDraft(CTX), schemaVersion: 1 };
    expect(parseDraft(JSON.stringify(old), CTX).ok).toBe(false);
    expect(
      parseDraft(JSON.stringify(old), CTX),
    ).toMatchObject({ reason: "wrong_version" });
  });

  it("rejeita rascunho de outro contexto — não mistura estudos", () => {
    const draft = emptyDraft(CTX);
    const other = { ...CTX, productCode: "999" };
    expect(parseDraft(JSON.stringify(draft), other)).toMatchObject({
      ok: false,
      reason: "wrong_context",
    });
    expect(
      parseDraft(JSON.stringify(draft), { ...CTX, branch: "02" }),
    ).toMatchObject({ ok: false, reason: "wrong_context" });
  });

  it("rejeita schema malformado (posts/inputs/activeId)", () => {
    const base = JSON.parse(JSON.stringify(emptyDraft(CTX)));
    base.scenarios[0].posts = [{ bogus: true }];
    expect(parseDraft(JSON.stringify(base), CTX).ok).toBe(false);
    const base2 = JSON.parse(JSON.stringify(emptyDraft(CTX)));
    base2.scenarios[0].inputs = { demand: 5 };
    expect(parseDraft(JSON.stringify(base2), CTX).ok).toBe(false);
    const base3 = JSON.parse(JSON.stringify(emptyDraft(CTX)));
    base3.activeScenarioId = "inexistente";
    expect(parseDraft(JSON.stringify(base3), CTX).ok).toBe(false);
  });

  it("removeDraft remove só a chave alvo", () => {
    const storage = memoryStorage();
    const key = buildStorageKey("u", CTX);
    const other = buildStorageKey("u", { ...CTX, branch: "02" });
    saveDraft(storage, key, emptyDraft(CTX));
    saveDraft(storage, other, emptyDraft({ ...CTX, branch: "02" }));
    expect(removeDraft(storage, key)).toBe(true);
    expect(loadDraft(storage, key)).toBeNull();
    expect(loadDraft(storage, other)).not.toBeNull();
  });

  it("storage indisponível → unavailable, sem lançar", () => {
    expect(saveDraft(null, "k", emptyDraft(CTX))).toBe("unavailable");
    expect(loadDraft(null, "k")).toBeNull();
    expect(removeDraft(null, "k")).toBe(false);
  });
});

describe("inputsFingerprint", () => {
  it("detecta mudança de parâmetros — base do STALE", () => {
    const a = inputsFingerprint({ demand: 500, available_minutes: 420 });
    expect(
      inputsFingerprint({ demand: 500, available_minutes: 420 }),
    ).toBe(a);
    expect(
      inputsFingerprint({ demand: 600, available_minutes: 420 }),
    ).not.toBe(a);
    expect(
      inputsFingerprint({
        demand: 500,
        available_minutes: 420,
        num_stations: 2,
      }),
    ).not.toBe(a);
  });
});

describe("fábricas", () => {
  it("emptyDraft inicia com cenário A ativo e sem postos", () => {
    const d = emptyDraft(CTX);
    expect(d.schemaVersion).toBe(STUDY_SCHEMA_VERSION);
    expect(d.scenarios).toHaveLength(1);
    expect(d.scenarios[0].label).toBe("A");
    expect(d.scenarios[0].mode).toBe("quick");
    expect(d.activeScenarioId).toBe(d.scenarios[0].clientId);
  });

  it("clientIds são únicos e prefixados", () => {
    const a = newClientId("post");
    const b = newClientId("post");
    expect(a).not.toBe(b);
    expect(a).toMatch(/^post-/);
  });

  it("newScenarioDraft cria estrutura completa", () => {
    const s = newScenarioDraft("B");
    expect(s.label).toBe("B");
    expect(s.posts).toEqual([]);
    expect(s.inputs.demand).toBe("");
  });
});
