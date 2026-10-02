import { describe, expect, it } from "vitest";
import type { TvDataModel } from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  buildDataModelParamPatch,
  collectDataModelParamSchema,
  resolveDataModelOperationIds,
  resolveModelPrimaryRoute,
  resolveModelSharedParamValues,
} from "./dataModelParamProjection";

const routes: TvDataRouteCatalogItem[] = [
  {
    operationId: "route_a",
    category: "production",
    path: "/a",
    label: "Rota A",
    paramSchema: {
      branch: { type: "string", label: "Filial" },
      start_date: { type: "string", format: "date" },
      end_date: { type: "string", format: "date" },
      seg_a: { type: "string", label: "Só A" },
    },
  },
  {
    operationId: "route_b",
    category: "supplies",
    path: "/b",
    label: "Rota B",
    paramSchema: {
      branch: { type: "string", label: "Filial" },
      start_date: { type: "string", format: "date" },
      end_date: { type: "string", format: "date" },
      seg_b: { type: "string", label: "Só B" },
    },
    fixedQueryParams: { token: "fixed" },
  },
];

const model: TvDataModel = {
  id: "m1",
  label: "Modelo",
  primaryInputId: "in_a",
  inputs: [
    {
      id: "in_a",
      operationId: "route_a",
      params: { branch: "01", seg_a: "keep-a" },
      transform: "input.rows",
    },
    {
      id: "in_b",
      operationId: "route_b",
      params: { branch: "01", seg_b: "keep-b" },
    },
  ] as TvDataModel["inputs"],
  fieldLabels: { total: "Total" },
  transform: "rows",
} as TvDataModel;

describe("dataModelParamProjection", () => {
  it("resolveDataModelOperationIds coleta operationIds dos inputs (dedup)", () => {
    const dup = {
      ...model,
      inputs: [
        { id: "x", operationId: "route_a" },
        { id: "y", operationId: "route_a" },
        { id: "z", operationId: "route_b" },
      ],
    } as TvDataModel;
    expect(resolveDataModelOperationIds(dup).sort()).toEqual(["route_a", "route_b"]);
  });

  it("collectDataModelParamSchema une rotas dos inputs sem paginação/fixos", () => {
    const { schema, conflicts } = collectDataModelParamSchema(routes, model);
    expect(schema.branch).toBeTruthy();
    expect(schema.seg_a).toBeTruthy();
    expect(schema.seg_b).toBeTruthy();
    expect(schema.token).toBeUndefined(); // fixedQueryParams nunca aparece
    expect(conflicts).toEqual([]);
  });

  it("resolveModelPrimaryRoute prefere primaryInputId", () => {
    expect(resolveModelPrimaryRoute(routes, model)?.operationId).toBe("route_a");
    const noPrimary = { ...model, primaryInputId: "missing" } as TvDataModel;
    expect(resolveModelPrimaryRoute(routes, noPrimary)?.operationId).toBe("route_a");
  });

  it("valores compartilhados: branch igual nos dois inputs; seg_* marcam partial", () => {
    const { schema } = collectDataModelParamSchema(routes, model);
    const shared = resolveModelSharedParamValues(model, routes, schema);
    expect(shared.values.branch).toBe("01");
    expect(shared.divergedKeys.has("branch")).toBe(false);
    expect(shared.partialKeys.has("seg_a")).toBe(true);
    expect(shared.partialKeys.has("seg_b")).toBe(true);
    expect(shared.partialKeys.has("branch")).toBe(false);
  });

  it("inputs divergentes viram divergedKeys (valor agregado limpo)", () => {
    const diverged = {
      ...model,
      inputs: [
        { ...model.inputs[0], params: { branch: "01" } },
        { ...model.inputs[1], params: { branch: "02" } },
      ],
    } as TvDataModel;
    const { schema } = collectDataModelParamSchema(routes, diverged);
    const shared = resolveModelSharedParamValues(diverged, routes, schema);
    expect(shared.divergedKeys.has("branch")).toBe(true);
    expect(shared.values.branch).toBe("");
  });

  it("DATAMODEL_EXPRESSIONS_PRESERVED: ExpressionSpec compartilhado sobrevive intacto", () => {
    const spec = {
      expression: {
        ast: { kind: "literal", value: "01" },
        source: '"01"',
      },
    };
    const withExpr = {
      ...model,
      inputs: [
        { ...model.inputs[0], params: { branch: spec } },
        { ...model.inputs[1], params: { branch: spec } },
      ],
    } as TvDataModel;
    const { schema } = collectDataModelParamSchema(routes, withExpr);
    const shared = resolveModelSharedParamValues(withExpr, routes, schema);
    expect(shared.values.branch).toEqual(spec);
    expect(shared.divergedKeys.has("branch")).toBe(false);
  });

  it("MODEL_LEVEL_SHARED_FILTER_EDIT: update agregado faz fan-out só nos inputs compatíveis", () => {
    const next = buildDataModelParamPatch(model, routes, { branch: "02" });
    expect(next).not.toBeNull();
    expect(next!.inputs[0]!.params?.branch).toBe("02");
    expect(next!.inputs[1]!.params?.branch).toBe("02");
  });

  it("MODEL_INPUT_SPECIFIC_PARAMS_PRESERVED: fan-out preserva demais params/campos", () => {
    const next = buildDataModelParamPatch(model, routes, {
      branch: "02",
      seg_a: "new-a",
    });
    expect(next).not.toBeNull();
    const [a, b] = next!.inputs;
    // input A recebeu as duas chaves; input B só branch (seg_a não existe na rota B)
    expect(a!.params).toMatchObject({ branch: "02", seg_a: "new-a" });
    expect(b!.params).toMatchObject({ branch: "02", seg_b: "keep-b" });
    expect(b!.params?.seg_a).toBeUndefined();
    // campos estruturais preservados
    expect(a!.id).toBe("in_a");
    expect(a!.operationId).toBe("route_a");
    expect(a!.transform).toBe("input.rows");
    expect(next!.transform).toBe("rows");
    expect(next!.fieldLabels).toEqual({ total: "Total" });
    expect(next!.primaryInputId).toBe("in_a");
  });

  it("patch mínimo: update sem efeito retorna null (sem save desnecessário)", () => {
    const next = buildDataModelParamPatch(model, routes, { branch: "01" });
    expect(next).toBeNull();
  });

  it("chave inexistente em nenhum schema não gera patch", () => {
    const next = buildDataModelParamPatch(model, routes, { unknown_xyz: "v" });
    expect(next).toBeNull();
  });

  it("preset de período aplica em todos os inputs (chave sintetizada)", () => {
    const next = buildDataModelParamPatch(model, routes, {
      dateRangePreset: "this_month",
    });
    expect(next).not.toBeNull();
    expect(next!.inputs[0]!.params?.dateRangePreset).toBe("this_month");
    expect(next!.inputs[1]!.params?.dateRangePreset).toBe("this_month");
  });
});
