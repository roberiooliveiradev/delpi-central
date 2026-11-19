import { deepStrictEqual, equal, match, ok } from "node:assert/strict";
import { test } from "node:test";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildSync } from "esbuild";

const root = fileURLToPath(new URL("..", import.meta.url));
const outDir = mkdtempSync(path.join(tmpdir(), "lbs-help-"));
const outfile = path.join(outDir, "helpCatalog.mjs");
buildSync({
  entryPoints: [path.join(root, "src/ui/helpCatalog.ts")],
  bundle: true, format: "esm", outfile, logLevel: "silent",
});
const catalog = await import(outfile);
const {
  STUDIO_HELP_GROUPS, METHOD_GUIDES,
  SOURCE_HELP, STUDY_HELP, PRODUCTION_HELP, BALANCE_HELP, METHOD_HELP, ACTION_HELP, STATE_HELP,
} = catalog;

const entries = Object.values(STUDIO_HELP_GROUPS).flatMap(group => Object.values(group));

test("every help entry has a stable id, title and a non-empty pt-BR summary", () => {
  ok(entries.length >= 50, `expected a broad catalog, got ${entries.length}`);
  const ids = new Set(entries.map(entry => entry.id));
  equal(ids.size, entries.length, "ids must be unique");
  for (const entry of entries) {
    match(entry.id, /^[a-z]+\.[a-zA-Z][a-zA-Z0-9]*$/, `unexpected id shape: ${entry.id}`);
    ok(entry.title.length > 1 && entry.summary.length > 20, `${entry.id} needs real content`);
    match(entry.summary, /[a-záàâãéêíóôõúç]/i, `${entry.id} should read as pt-BR prose`);
  }
});

test("provenance vocabulary is complete and precise", () => {
  for (const key of ["observed", "provided", "calculated", "simulation", "unknown", "draftLocal"]) {
    ok(SOURCE_HELP[key], `missing source entry ${key}`);
  }
  match(SOURCE_HELP.observed.summary, /roteiro oficial/i);
  match(SOURCE_HELP.unknown.summary, /nunca assume|nunca.*zero/i);
  match(SOURCE_HELP.draftLocal.summary, /roteiro oficial/i);
  match(SOURCE_HELP.simulation.summary, /não é aprovação/i);
});

test("required technical terms exist in the catalog", () => {
  const required = {
    production: ["takt", "demand", "batch", "pause", "productiveTime", "standardTime", "setup", "shiftMode"],
    balance: ["operation", "station", "workCenter", "stationLoad", "maxLoad", "unassigned", "yamazumi", "taktVsLoad", "bottleneck", "resource"],
    method: ["m1", "m2", "m3", "m4", "m5", "m6", "planned", "rail"],
    study: ["product", "manualStudy", "routing", "branch", "stage", "scenario", "draftSave"],
  };
  for (const [group, keys] of Object.entries(required)) {
    for (const key of keys) ok(STUDIO_HELP_GROUPS[group][key], `missing ${group}.${key}`);
  }
});

test("planned methods are described as planned, never as executable", () => {
  for (const key of ["m2", "m3", "m4", "m6"]) {
    match(METHOD_HELP[key].summary, /[Pp]lanejado/, `${key} must read as planned`);
  }
  match(METHOD_HELP.m5.summary, /Yamazumi/i);
  match(METHOD_HELP.m1.summary, /takt/i);
});

test("CT is not conflated with a physical station", () => {
  match(BALANCE_HELP.workCenter.summary, /não é|não equivale/i);
  match(BALANCE_HELP.station.summary, /hipotético/i);
});

test("M1 and M5 guides have objective, steps, interpretation and limitations", () => {
  for (const id of ["M1", "M5"]) {
    const guide = METHOD_GUIDES[id];
    ok(guide, `missing guide ${id}`);
    ok(guide.objective.length > 30, `${id} objective`);
    ok(guide.steps.length >= 4, `${id} steps`);
    ok(guide.interpretation.length >= 3, `${id} interpretation`);
    ok(guide.limitations.length >= 3, `${id} limitations`);
    for (const section of [guide.objective, ...guide.steps, ...guide.interpretation, ...guide.limitations]) {
      ok(!/lorem ipsum/i.test(section) && !/^\s*todo\s*$/i.test(section.trim()),
        `${id} placeholder text detected`);
    }
  }
  match(METHOD_GUIDES.M1.limitations.join(" "), /UNKNOWN/i);
  match(METHOD_GUIDES.M5.limitations.join(" "), /SIMULATION/i);
  match(METHOD_GUIDES.M5.limitations.join(" "), /roteiro oficial/i);
});

test("state guidance points to the next action", () => {
  match(STATE_HELP.noStations.summary, /Crie um posto|posto/i);
  match(STATE_HELP.noTakt.summary, /turno|demanda/i);
  match(STATE_HELP.unknownTime.summary, /parcial/i);
  deepStrictEqual(
    Object.keys(STUDIO_HELP_GROUPS).sort(),
    ["action", "balance", "method", "production", "source", "state", "study"],
  );
});
