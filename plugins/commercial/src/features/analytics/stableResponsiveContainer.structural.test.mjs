#!/usr/bin/env node
/**
 * Gate: OTD insight e detalhe OP usam StableResponsiveContainer do kit
 * (não ResponsiveContainer cru do Recharts) — anti React #185 ao recolher sidebar.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const commercialSrc = join(here, "../..");

const FILES = [
  "features/analytics/components/AnalyticsOtdInsightBarChart.tsx",
  "components/OpenOrdersProductionDetailContent.tsx",
];

describe("stableResponsiveContainer — irmãos Comercial", () => {
  for (const rel of FILES) {
    it(`${rel} usa StableResponsiveContainer e não importa ResponsiveContainer de recharts`, () => {
      const source = readFileSync(join(commercialSrc, rel), "utf8");
      assert.match(source, /\bStableResponsiveContainer\b/);
      assert.doesNotMatch(
        source,
        /import\s*\{[^}]*\bResponsiveContainer\b[^}]*\}\s*from\s*["']recharts["']/,
        "não deve importar ResponsiveContainer de recharts",
      );
      const stripped = source.replace(/\bStableResponsiveContainer\b/g, "");
      assert.doesNotMatch(
        stripped,
        /\bResponsiveContainer\b/,
        "não deve restar JSX/uso cru de ResponsiveContainer",
      );
    });
  }
});
