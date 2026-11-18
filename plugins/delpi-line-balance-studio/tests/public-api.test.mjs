import { deepStrictEqual, equal, ok } from "node:assert/strict";
import { test } from "node:test";
import { createManualStudy, listMethods, summarizeShift } from "@delpi/line-balance-studio";

test("creates independent manual snapshots without a product or inferred time", () => {
  const input = {
    id: "pilot",
    name: "Linha piloto",
    operations: [
      { id: "assembly", name: "Montar", durationSeconds: 32.5 },
      { id: "inspection", name: "Inspecionar", durationSeconds: null },
    ],
    stations: [{ id: "A", name: "Posto A" }, { id: "B", name: "Posto B" }],
    scenarios: [
      { id: "current", name: "Atual", assignments: [{ operationId: "assembly", stationId: "A" }] },
      { id: "proposed", name: "Proposto", assignments: [{ operationId: "assembly", stationId: "B" }] },
    ],
    conditions: {
      shift: { mode: "CLOCK", start: "22:00", end: "06:00", breaks: [{ start: "01:00", end: "01:30" }] },
      demandUnitsPerShift: 200,
      batchUnits: 25,
    },
  };
  const result = createManualStudy(input);
  ok(result.ok);
  const { value } = result;
  input.conditions.shift.breaks[0].end = "02:00";
  input.scenarios[0].assignments[0].stationId = "B";
  input.operations[0].durationSeconds = 60;
  equal(value.schemaVersion, 1);
  equal(value.source, "MANUAL");
  equal(value.status, "DRAFT_LOCAL");
  equal("productCode" in value, false);
  deepStrictEqual(value.operations.map(operation => operation.time), [
    { durationSeconds: 32.5, provenance: "PROVIDED" },
    { durationSeconds: null, provenance: "UNKNOWN" },
  ]);
  deepStrictEqual(value.scenarios.map(scenario => [
    scenario.provenance, scenario.assignments.length, scenario.assignments[0].stationId,
  ]), [["SIMULATION", 1, "A"], ["SIMULATION", 1, "B"]]);
  equal(value.conditions.shift.breaks[0].end, "01:30");
  equal(value.conditions.summary.productiveMinutes, 450);
});

test("accepts an empty draft prior to entering operations and a shift", () => {
  const result = createManualStudy({ id: "new", name: "Estudo", operations: [], stations: [], scenarios: [] });
  ok(result.ok);
  equal("conditions" in result.value, false);
});

test("reports invalid references, duplicate IDs and assignments, and invalid values by path", () => {
  const result = createManualStudy({
    id: "study",
    name: "Linha piloto",
    operations: [
      { id: "op", name: "Montar", durationSeconds: Infinity },
      { id: "op", name: "Apertar", durationSeconds: 2 },
    ],
    stations: [{ id: "A", name: "  " }],
    scenarios: [{
      id: "s",
      name: "Cenário",
      assignments: [
        { operationId: "op", stationId: "A" },
        { operationId: "op", stationId: "B" },
        { operationId: "missing", stationId: "A" },
      ],
    }],
    conditions: {
      shift: { mode: "MINUTES", durationMinutes: 0, breaks: [] },
      demandUnitsPerShift: 1.5,
      batchUnits: 0,
    },
  });

  equal(result.ok, false);
  deepStrictEqual(result.issues, [
    { path: "operations[1].id", code: "DUPLICATE_ID" },
    { path: "stations[0].name", code: "REQUIRED" },
    { path: "operations[0].durationSeconds", code: "INVALID_NUMBER" },
    { path: "scenarios[0].assignments[1].stationId", code: "UNKNOWN_STATION" },
    { path: "scenarios[0].assignments[1].operationId", code: "DUPLICATE_ASSIGNMENT" },
    { path: "scenarios[0].assignments[2].operationId", code: "UNKNOWN_OPERATION" },
    { path: "conditions.demandUnitsPerShift", code: "INVALID_NUMBER" },
    { path: "conditions.batchUnits", code: "INVALID_NUMBER" },
    { path: "conditions.shift.durationMinutes", code: "INVALID_NUMBER" },
  ]);
});

test("exposes the six methods without marking planned capabilities as runnable", () => {
  const methods = listMethods();
  deepStrictEqual(methods.map(method => method.id), ["M1", "M2", "M3", "M4", "M5", "M6"]);
  ok(methods.every(method => method.status === "PLANNED"));
  deepStrictEqual(methods.filter(method => method.next).map(method => method.id), ["M5"]);
  methods[0].status = "AVAILABLE";
  equal(listMethods()[0].status, "PLANNED");
});

test("calculates equivalent day shifts by clock or by direct durations", () => {
  const clock = summarizeShift({
    mode: "CLOCK", start: "08:00", end: "17:00",
    breaks: [{ start: "15:00", end: "15:15" }, { start: "12:00", end: "13:00" }],
  });
  const direct = summarizeShift({ mode: "MINUTES", durationMinutes: 540, breaks: [60, 15] });
  deepStrictEqual(clock, direct);
  deepStrictEqual(clock.value, {
    grossMinutes: 540, breakMinutes: 75, productiveMinutes: 465, provenance: "CALCULATED",
  });
});

test("handles adjacent overnight breaks including midnight and the shift end", () => {
  const result = summarizeShift({
    mode: "CLOCK", start: "22:00", end: "06:00",
    breaks: [
      { start: "05:55", end: "06:00" },
      { start: "00:10", end: "00:20" },
      { start: "23:50", end: "00:10" },
    ],
  });
  ok(result.ok);
  equal(result.value.productiveMinutes, 445);
});

test("rejects overlapping, empty, out-of-shift and malformed pause intervals", () => {
  const result = summarizeShift({
    mode: "CLOCK", start: "22:00", end: "06:00",
    breaks: [
      { start: "00:05", end: "00:25" },
      { start: "23:55", end: "00:10" },
      { start: "21:50", end: "22:05" },
      { start: "05:50", end: "06:10" },
      { start: "03:00", end: "03:00" },
      { start: "24:00", end: "02:00" },
    ],
  });
  equal(result.ok, false);
  deepStrictEqual(result.issues, [
    { path: "breaks[2]", code: "BREAK_OUTSIDE_SHIFT" },
    { path: "breaks[3]", code: "BREAK_OUTSIDE_SHIFT" },
    { path: "breaks[4]", code: "EMPTY_BREAK" },
    { path: "breaks[5].start", code: "INVALID_CLOCK_TIME" },
    { path: "breaks[0]", code: "BREAK_OVERLAP" },
  ]);
});

test("rejects ambiguous or exhausted shifts and applies the 24-hour bound", () => {
  const cases = [
    [{ mode: "CLOCK", start: "06:00", end: "06:00", breaks: [] }, "AMBIGUOUS_SHIFT"],
    [{ mode: "CLOCK", start: "08:00", end: "09:00", breaks: [{ start: "08:00", end: "09:00" }] }, "NO_PRODUCTIVE_TIME"],
    [{ mode: "MINUTES", durationMinutes: 480, breaks: [480, 15] }, "NO_PRODUCTIVE_TIME"],
    [{ mode: "MINUTES", durationMinutes: 480, breaks: [-1, 1.2] }, "INVALID_NUMBER"],
    [{ mode: "MINUTES", durationMinutes: 1441, breaks: [] }, "INVALID_NUMBER"],
  ];
  for (const [input, code] of cases) {
    const result = summarizeShift(input);
    equal(result.ok, false);
    equal(result.issues[0].code, code);
  }
  equal(summarizeShift({ mode: "MINUTES", durationMinutes: 1440, breaks: [] }).ok, true);
});
