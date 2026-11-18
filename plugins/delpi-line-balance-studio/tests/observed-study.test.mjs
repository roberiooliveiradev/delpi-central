import test from "node:test";
import assert from "node:assert/strict";
import { createObservedStudy, createManualStudy } from "../dist/index.js";

const routing = { productCode: "90264302", branchCode: "01", stageId: "90264302#0", stageLabel: "Estágio 0 — 90264302" };
const base = {
  id: "study-1", name: "Estudo oficial", source: "OBSERVED_ROUTING", routing,
  operations: [
    { id: "op-a", name: "Corte", durationSeconds: 120, reference: "OP 010 · CT 900" },
    { id: "op-b", name: "Solda", durationSeconds: null },
  ],
  stations: [{ id: "st-1", name: "Posto 01" }],
  scenarios: [{ id: "sc-a", name: "Cenário A", assignments: [{ operationId: "op-a", stationId: "st-1" }] }],
};

test("creates OBSERVED_ROUTING study with OBSERVED and UNKNOWN times", () => {
  const result = createObservedStudy(base);
  assert.equal(result.ok, true);
  assert.equal(result.value.source, "OBSERVED_ROUTING");
  assert.equal(result.value.status, "DRAFT_LOCAL");
  assert.equal(result.value.routing.productCode, "90264302");
  assert.equal(result.value.operations[0].time.provenance, "OBSERVED");
  assert.equal(result.value.operations[1].time.provenance, "UNKNOWN");
  assert.equal(result.value.scenarios[0].provenance, "SIMULATION");
});

test("missing times stay UNKNOWN — never zeroed", () => {
  const result = createObservedStudy({
    ...base,
    operations: [{ id: "op-x", name: "Sem tempo", durationSeconds: null }],
    scenarios: [{ id: "sc-a", name: "Cenário A", assignments: [] }],
  });
  assert.equal(result.ok, true);
  assert.deepEqual(result.value.operations[0].time, { durationSeconds: null, provenance: "UNKNOWN" });
});

test("rejects missing routing identity", () => {
  const result = createObservedStudy({ ...base, routing: { productCode: "", branchCode: "", stageId: "" } });
  assert.equal(result.ok, false);
  assert.ok(result.issues.some(i => i.path === "routing.productCode" && i.code === "REQUIRED"));
  assert.ok(result.issues.some(i => i.path === "routing.branchCode"));
  assert.ok(result.issues.some(i => i.path === "routing.stageId"));
});

test("rejects invalid times and unknown assignments", () => {
  const result = createObservedStudy({
    ...base,
    operations: [{ id: "op-a", name: "Corte", durationSeconds: -5 }],
    scenarios: [{ id: "sc-a", name: "A", assignments: [{ operationId: "ghost", stationId: "st-1" }] }],
  });
  assert.equal(result.ok, false);
  assert.ok(result.issues.some(i => i.code === "INVALID_NUMBER"));
  assert.ok(result.issues.some(i => i.code === "UNKNOWN_OPERATION"));
});

test("manual study contract unchanged by the additive input", () => {
  const manual = { id: "m", name: "Manual", operations: [], stations: [], scenarios: [] };
  const result = createManualStudy(manual);
  assert.equal(result.ok, true);
  assert.equal(result.value.source, "MANUAL");
});
