import { summarizeShift, type ShiftInput, type ShiftSummary } from "./shift.js";
import type { ValidationIssue, ValidationResult } from "./validation.js";

type NamedItem = Readonly<{ id: string; name: string }>;

export type ManualOperationInput = NamedItem & Readonly<{ durationSeconds: number | null }>;
export type Station = NamedItem;
export type Assignment = Readonly<{ operationId: string; stationId: string }>;
export type ScenarioInput = NamedItem & Readonly<{ assignments: readonly Assignment[] }>;

export type ProductionConditionsInput = Readonly<{
  shift: ShiftInput;
  demandUnitsPerShift?: number;
  batchUnits?: number;
}>;

export type ManualStudyInput = NamedItem & Readonly<{
  operations: readonly ManualOperationInput[];
  stations: readonly Station[];
  scenarios: readonly ScenarioInput[];
  conditions?: ProductionConditionsInput;
}>;

type OperationTime =
  | Readonly<{ durationSeconds: number; provenance: "PROVIDED" }>
  | Readonly<{ durationSeconds: null; provenance: "UNKNOWN" }>;

export type ManualOperation = NamedItem & Readonly<{ time: OperationTime }>;
export type StudyScenario = ScenarioInput & Readonly<{ provenance: "SIMULATION" }>;

export type ManualStudy = NamedItem & Readonly<{
  schemaVersion: 1;
  source: "MANUAL";
  status: "DRAFT_LOCAL";
  operations: readonly ManualOperation[];
  stations: readonly Station[];
  scenarios: readonly StudyScenario[];
  conditions?: ProductionConditionsInput & Readonly<{ summary: ShiftSummary }>;
}>;

function checkName(item: NamedItem, path: string, issues: ValidationIssue[]): void {
  const prefix = path ? `${path}.` : "";
  if (!item.id.trim()) issues.push({ path: `${prefix}id`, code: "REQUIRED" });
  if (!item.name.trim()) issues.push({ path: `${prefix}name`, code: "REQUIRED" });
}

function collectIds(
  items: readonly NamedItem[],
  collection: string,
  issues: ValidationIssue[],
): Set<string> {
  const ids = new Set<string>();
  items.forEach((item, index) => {
    const path = `${collection}[${index}]`;
    checkName(item, path, issues);
    if (ids.has(item.id)) issues.push({ path: `${path}.id`, code: "DUPLICATE_ID" });
    ids.add(item.id);
  });
  return ids;
}

function copyShift(shift: ShiftInput): ShiftInput {
  if (shift.mode === "MINUTES") {
    return { mode: shift.mode, durationMinutes: shift.durationMinutes, breaks: [...shift.breaks] };
  }
  return {
    mode: shift.mode,
    start: shift.start,
    end: shift.end,
    breaks: shift.breaks.map(({ start, end }) => ({ start, end })),
  };
}

export function createManualStudy(input: ManualStudyInput): ValidationResult<ManualStudy> {
  const issues: ValidationIssue[] = [];
  checkName(input, "", issues);
  const operationIds = collectIds(input.operations, "operations", issues);
  const stationIds = collectIds(input.stations, "stations", issues);
  collectIds(input.scenarios, "scenarios", issues);

  const operations = input.operations.map(({ id, name, durationSeconds }, index): ManualOperation => {
    if (durationSeconds !== null && (!Number.isFinite(durationSeconds) || durationSeconds <= 0)) {
      issues.push({ path: `operations[${index}].durationSeconds`, code: "INVALID_NUMBER" });
    }
    return {
      id,
      name,
      time: durationSeconds === null
        ? { durationSeconds, provenance: "UNKNOWN" }
        : { durationSeconds, provenance: "PROVIDED" },
    };
  });

  const scenarios = input.scenarios.map(({ id, name, assignments }, index): StudyScenario => {
    const assigned = new Set<string>();
    const snapshot = assignments.map(({ operationId, stationId }, assignmentIndex) => {
      const path = `scenarios[${index}].assignments[${assignmentIndex}]`;
      if (!operationIds.has(operationId)) {
        issues.push({ path: `${path}.operationId`, code: "UNKNOWN_OPERATION" });
      }
      if (!stationIds.has(stationId)) {
        issues.push({ path: `${path}.stationId`, code: "UNKNOWN_STATION" });
      }
      if (assigned.has(operationId)) {
        issues.push({ path: `${path}.operationId`, code: "DUPLICATE_ASSIGNMENT" });
      }
      assigned.add(operationId);
      return { operationId, stationId };
    });
    return { id, name, assignments: snapshot, provenance: "SIMULATION" };
  });

  let conditions: ManualStudy["conditions"];
  if (input.conditions) {
    const { shift, demandUnitsPerShift, batchUnits } = input.conditions;
    const summary = summarizeShift(shift);
    for (const [field, value] of Object.entries({ demandUnitsPerShift, batchUnits })) {
      if (value !== undefined && (!Number.isSafeInteger(value) || value <= 0)) {
        issues.push({ path: `conditions.${field}`, code: "INVALID_NUMBER" });
      }
    }
    if (summary.ok) {
      conditions = {
        shift: copyShift(shift),
        summary: summary.value,
        ...(demandUnitsPerShift === undefined ? {} : { demandUnitsPerShift }),
        ...(batchUnits === undefined ? {} : { batchUnits }),
      };
    } else {
      issues.push(...summary.issues.map(issue => ({ ...issue, path: `conditions.shift.${issue.path}` })));
    }
  }

  if (issues.length) return { ok: false, issues };
  return {
    ok: true,
    value: {
      id: input.id,
      name: input.name,
      schemaVersion: 1,
      source: "MANUAL",
      status: "DRAFT_LOCAL",
      operations,
      stations: input.stations.map(({ id, name }) => ({ id, name })),
      scenarios,
      ...(conditions === undefined ? {} : { conditions }),
    },
  };
}
