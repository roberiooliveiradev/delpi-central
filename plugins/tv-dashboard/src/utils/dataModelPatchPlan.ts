/**
 * Diff entre o DataModel persistido e o draft editado → patch mínimo
 * `patch_data_model` (TV-DM-MUT-002). Campos omitidos no patch são
 * preservados pelo backend; nunca reenviar o modelo inteiro para edições
 * pontuais. Mudanças estruturais (inputs adicionados/removidos/reordenados,
 * operationId/queryName/label de input, primaryInputId) não são patcheáveis
 * e exigem `upsert_data_model` (full replace) — retornadas como "replace".
 */

import type { TvDataModel } from "@delpi/tv-dashboard-presentation";

export type DataModelInputPatch = {
  inputId: string;
  params?: { set?: Record<string, unknown>; unset?: string[] };
  transform?: unknown | null;
};

export type DataModelPatchPlan = {
  modelId: string;
  inputPatches?: DataModelInputPatch[];
  modelPatch?: {
    label?: string;
    transform?: unknown | null;
    fieldLabels?: Record<string, string> | null;
  };
};

export type DataModelEditPlan =
  | { kind: "noop" }
  | { kind: "patch"; patch: DataModelPatchPlan }
  | { kind: "replace" };

function stableJson(value: unknown): string {
  if (value === null || typeof value !== "object") return JSON.stringify(value ?? null);
  if (Array.isArray(value)) return `[${value.map(stableJson).join(",")}]`;
  const entries = Object.keys(value as Record<string, unknown>)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stableJson((value as Record<string, unknown>)[key])}`);
  return `{${entries.join(",")}}`;
}

function sameTransform(a: unknown, b: unknown): boolean {
  const left = a == null ? null : a;
  const right = b == null ? null : b;
  return stableJson(left) === stableJson(right);
}

function diffParams(
  current: Record<string, unknown> | undefined,
  next: Record<string, unknown> | undefined,
): DataModelInputPatch["params"] | undefined {
  const left = current ?? {};
  const right = next ?? {};
  const set: Record<string, unknown> = {};
  const unset: string[] = [];
  for (const [key, value] of Object.entries(right)) {
    if (!(key in left) || stableJson(left[key]) !== stableJson(value)) set[key] = value;
  }
  for (const key of Object.keys(left)) {
    if (!(key in right)) unset.push(key);
  }
  if (Object.keys(set).length === 0 && unset.length === 0) return undefined;
  return { ...(Object.keys(set).length ? { set } : {}), ...(unset.length ? { unset } : {}) };
}

/**
 * Merge-map para `modelPatch.fieldLabels`: entradas alteradas/adicionadas com
 * o novo valor e removidas com `""` (o backend dropa valores vazios no merge).
 * `null` limpa o mapa inteiro; `undefined` = sem mudança.
 */
export function buildFieldLabelsMergePatch(
  current: Record<string, string> | undefined,
  next: Record<string, string> | undefined,
): Record<string, string> | null | undefined {
  const left = current ?? {};
  const right = next ?? {};
  if (Object.keys(right).length === 0) {
    return Object.keys(left).length ? null : undefined;
  }
  const merged: Record<string, string> = {};
  let changed = false;
  for (const [key, value] of Object.entries(right)) {
    if (left[key] !== value) {
      merged[key] = value;
      changed = true;
    }
  }
  for (const key of Object.keys(left)) {
    if (!(key in right)) {
      merged[key] = "";
      changed = true;
    }
  }
  return changed ? merged : undefined;
}

/**
 * Compara `existing` (persistido) com `next` (draft). "noop" quando nada do
 * contrato persistido muda; "replace" quando a edição é estrutural.
 */
export function buildDataModelEditPlan(
  existing: TvDataModel,
  next: TvDataModel,
): DataModelEditPlan {
  const existingInputs = existing.inputs ?? [];
  const nextInputs = next.inputs ?? [];
  const sameInputOrder =
    existingInputs.length === nextInputs.length &&
    existingInputs.every((item, index) => item.id === nextInputs[index]?.id);
  if (!sameInputOrder || existing.primaryInputId !== next.primaryInputId) {
    return { kind: "replace" };
  }
  for (let index = 0; index < existingInputs.length; index += 1) {
    const before = existingInputs[index]!;
    const after = nextInputs[index]!;
    if (
      before.operationId !== after.operationId ||
      (before.queryName ?? "") !== (after.queryName ?? "") ||
      (before.label ?? "") !== (after.label ?? "")
    ) {
      return { kind: "replace" };
    }
  }

  const inputPatches: DataModelInputPatch[] = [];
  for (let index = 0; index < existingInputs.length; index += 1) {
    const before = existingInputs[index]!;
    const after = nextInputs[index]!;
    const patch: DataModelInputPatch = { inputId: after.id };
    const params = diffParams(before.params, after.params);
    if (params) patch.params = params;
    if (!sameTransform(before.transform, after.transform)) {
      patch.transform = after.transform ?? null;
    }
    if (patch.params || "transform" in patch) inputPatches.push(patch);
  }

  const modelPatch: NonNullable<DataModelPatchPlan["modelPatch"]> = {};
  if ((existing.label ?? "") !== (next.label ?? "")) {
    modelPatch.label = next.label ?? "";
  }
  if (!sameTransform(existing.transform, next.transform)) {
    modelPatch.transform = next.transform ?? null;
  }
  const fieldLabels = buildFieldLabelsMergePatch(existing.fieldLabels, next.fieldLabels);
  if (fieldLabels !== undefined) modelPatch.fieldLabels = fieldLabels;

  if (inputPatches.length === 0 && Object.keys(modelPatch).length === 0) {
    return { kind: "noop" };
  }
  const patch: DataModelPatchPlan = { modelId: next.id };
  if (inputPatches.length) patch.inputPatches = inputPatches;
  if (Object.keys(modelPatch).length) patch.modelPatch = modelPatch;
  return { kind: "patch", patch };
}
