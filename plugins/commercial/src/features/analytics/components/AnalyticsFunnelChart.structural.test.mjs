#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = join(here, "../../..");

describe("AnalyticsFunnelChart — trapézio", () => {
  it("usa layout cm-funnel com taxa/meta e 3 etapas", () => {
    const source = readFileSync(join(here, "AnalyticsFunnelChart.tsx"), "utf8");
    assert.match(source, /cm-funnel/);
    assert.match(source, /Taxa de conversão/);
    assert.match(source, /Meta do período/);
    assert.match(source, /Propostas no período/);
    assert.match(source, /Ganhas \(aceite no período\)/);
    assert.match(source, /Sem conversão/);
    assert.match(source, /clip-path|cm-funnel__stage-inner/);
    assert.match(source, /CommercialTabularExportButtons/);
    assert.match(source, /buildOverviewFunnelPayload/);
    assert.doesNotMatch(source, /BarChart|recharts/);
  });

  it("CSS domínio cm-funnel sem espelho delpi-ui", () => {
    const css = readFileSync(join(srcRoot, "styles/funnel.css"), "utf8");
    assert.match(css, /\.cm-funnel__/);
    assert.doesNotMatch(css, /\.delpi-ui-/);
  });
});
