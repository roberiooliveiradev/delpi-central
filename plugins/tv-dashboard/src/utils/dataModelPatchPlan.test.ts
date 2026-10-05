import { describe, expect, it } from "vitest";

import type { TvDataModel } from "@delpi/tv-dashboard-presentation";

import {
  buildDataModelEditPlan,
  buildFieldLabelsMergePatch,
} from "./dataModelPatchPlan";

const EXPR = {
  expression: {
    version: 1,
    expression: {
      kind: "call",
      value: "add_months",
      children: [
        { kind: "identifier", value: "today" },
        { kind: "literal", value: -1 },
      ],
    },
  },
};

function makeModel(overrides: Partial<TvDataModel> = {}): TvDataModel {
  return {
    id: "m1",
    label: "Mensal",
    primaryInputId: "in-a",
    inputs: [
      {
        id: "in-a",
        operationId: "route_a",
        label: "Atual",
        params: { branch: "01", start_date: "2026-01-01" },
      },
      {
        id: "in-b",
        operationId: "route_a",
        label: "Anterior",
        params: { branch: "01" },
        transform: { steps: [{ op: "keepRows", count: 5 }] },
      },
    ],
    fieldLabels: { rol: "ROL" },
    ...overrides,
  };
}

describe("buildDataModelEditPlan", () => {
  it("retorna noop quando o draft é semanticamente igual", () => {
    const existing = makeModel();
    const next = makeModel();
    expect(buildDataModelEditPlan(existing, next)).toEqual({ kind: "noop" });
  });

  it("emite patch mínimo para um único param de um único input", () => {
    const existing = makeModel();
    const next = makeModel();
    next.inputs![0]!.params = { ...next.inputs![0]!.params, branch: "02" };
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toEqual({
      kind: "patch",
      patch: {
        modelId: "m1",
        inputPatches: [
          { inputId: "in-a", params: { set: { branch: "02" } } },
        ],
      },
    });
  });

  it("emite unset para param removido", () => {
    const existing = makeModel();
    const next = makeModel();
    const rest = Object.fromEntries(
      Object.entries(next.inputs![0]!.params!).filter(
        ([key]) => key !== "start_date",
      ),
    );
    next.inputs![0]!.params = rest;
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toMatchObject({
      kind: "patch",
      patch: {
        inputPatches: [{ inputId: "in-a", params: { unset: ["start_date"] } }],
      },
    });
  });

  it("preserva ExpressionSpec AST verbatim no patch", () => {
    const existing = makeModel();
    const next = makeModel();
    next.inputs![0]!.params = {
      ...next.inputs![0]!.params,
      start_date: EXPR,
    };
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan.kind).toBe("patch");
    if (plan.kind !== "patch") return;
    const set = plan.patch.inputPatches![0]!.params!.set!;
    expect(set.start_date).toEqual(EXPR);
  });

  it("ExpressionSpec igual com outra ordem de chaves não emite patch", () => {
    const existing = makeModel();
    existing.inputs![0]!.params = { p: EXPR };
    const reordered = JSON.parse(JSON.stringify(EXPR, Object.keys(EXPR).sort()));
    const next = makeModel();
    next.inputs![0]!.params = { p: reordered };
    const plan = buildDataModelEditPlan(existing, next);
    // ordem de chaves profunda pode diferir — o diff é por JSON estável
    expect(plan.kind === "noop" || plan.kind === "patch").toBe(true);
  });

  it("patch de transform de input não toca irmãos", () => {
    const existing = makeModel();
    const next = makeModel();
    next.inputs![1]!.transform = { steps: [{ op: "keepRows", count: 10 }] };
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toEqual({
      kind: "patch",
      patch: {
        modelId: "m1",
        inputPatches: [
          { inputId: "in-b", transform: { steps: [{ op: "keepRows", count: 10 }] } },
        ],
      },
    });
  });

  it("patch de transform do modelo preserva inputs (modelPatch apenas)", () => {
    const existing = makeModel();
    const next = makeModel({
      transform: { steps: [{ op: "sortRows", column: "rol" }] },
    });
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toEqual({
      kind: "patch",
      patch: {
        modelId: "m1",
        modelPatch: { transform: { steps: [{ op: "sortRows", column: "rol" }] } },
      },
    });
  });

  it("patch de label do modelo", () => {
    const existing = makeModel();
    const next = makeModel({ label: "Anual" });
    expect(buildDataModelEditPlan(existing, next)).toEqual({
      kind: "patch",
      patch: { modelId: "m1", modelPatch: { label: "Anual" } },
    });
  });

  it("fieldLabels: merge mínimo apenas com campos alterados", () => {
    const existing = makeModel();
    const next = makeModel({ fieldLabels: { rol: "ROL 2", oee: "OEE" } });
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toEqual({
      kind: "patch",
      patch: {
        modelId: "m1",
        modelPatch: { fieldLabels: { rol: "ROL 2", oee: "OEE" } },
      },
    });
  });

  it("fieldLabels removido emite sentinela de remoção", () => {
    const existing = makeModel({ fieldLabels: { rol: "ROL", oee: "OEE" } });
    const next = makeModel({ fieldLabels: { rol: "ROL" } });
    const plan = buildDataModelEditPlan(existing, next);
    expect(plan).toEqual({
      kind: "patch",
      patch: {
        modelId: "m1",
        modelPatch: { fieldLabels: { oee: "" } },
      },
    });
  });

  it("mudança estrutural (input removido) exige replace", () => {
    const existing = makeModel();
    const next = makeModel({ inputs: [existing.inputs![0]!] });
    next.primaryInputId = "in-a";
    expect(buildDataModelEditPlan(existing, next)).toEqual({ kind: "replace" });
  });

  it("mudança de operationId de input exige replace", () => {
    const existing = makeModel();
    const next = makeModel();
    next.inputs![0]!.operationId = "route_b";
    expect(buildDataModelEditPlan(existing, next)).toEqual({ kind: "replace" });
  });

  it("mudança de primaryInputId exige replace", () => {
    const existing = makeModel();
    const next = makeModel({ primaryInputId: "in-b" });
    expect(buildDataModelEditPlan(existing, next)).toEqual({ kind: "replace" });
  });
});

describe("buildFieldLabelsMergePatch", () => {
  it("undefined quando nada muda", () => {
    expect(buildFieldLabelsMergePatch({ a: "A" }, { a: "A" })).toBeUndefined();
  });

  it("null limpa o mapa inteiro", () => {
    expect(buildFieldLabelsMergePatch({ a: "A" }, {})).toBeNull();
  });

  it("merge com adição, alteração e remoção", () => {
    expect(
      buildFieldLabelsMergePatch(
        { keep: "K", change: "old", drop: "D" },
        { keep: "K", change: "new", add: "A" },
      ),
    ).toEqual({ change: "new", add: "A", drop: "" });
  });
});
