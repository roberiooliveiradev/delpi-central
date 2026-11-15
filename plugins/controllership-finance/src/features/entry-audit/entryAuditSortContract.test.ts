/**
 * U12 R2 / W2 — contrato: colunas `sortable` do MFE (serverSort) ⊆ whitelist BFF
 * **por aba/recurso** (não pela união).
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

import { ENTRY_AUDIT_TABS, entryAuditTabResource } from "./entryAuditPresentation";

const ANALYSIS_PAGE = join(__dirname, "EntryAuditAnalysisPage.tsx");

/** Espelho de controllership_finance_app/application/entry_audit/service.py */
const WHITELIST_BY_RESOURCE: Record<string, ReadonlySet<string>> = {
  occurrences: new Set([
    "severity",
    "supplier",
    "document",
    "day",
    "difference",
    "theme",
    "status",
    "rule",
    "field",
    "protheus",
    "xml",
  ]),
  documents: new Set([
    "document_number",
    "received_date",
    "issue_date",
    "supplier_name",
    "amount",
    "situation",
    "series",
    "branch",
    "access_key",
  ]),
  unmatched: new Set([
    "document_number",
    "supplier_name",
    "situation",
    "series",
    "branch",
    "nature",
    "received_date",
    "amount",
    "access_key",
  ]),
  cte: new Set([
    "document_number",
    "branch",
    "access_key",
    "series",
    "supplier_name",
    "amount",
    "received_date",
  ]),
  tes: new Set(["tes_code", "items", "description", "branch"]),
};

function extractOccurrenceSortKeys(source: string): string[] {
  const block = source.match(
    /const occurrenceColumns[\s\S]*?=[\s\S]*?\[([\s\S]*?)\];/,
  )?.[1];
  if (!block) return [];
  return [...block.matchAll(/key:\s*"([^"]+)"[\s\S]*?sortable:\s*true/g)].map(
    (m) => m[1],
  );
}

/** Resolve a chave efetiva de uma coluna genérica para a aba dada. */
function resolveGenericKeysForTab(source: string, tab: string): string[] {
  const block = source.match(
    /const genericColumns[\s\S]*?=[\s\S]*?\[([\s\S]*?)\];/,
  )?.[1];
  if (!block) return [];
  const keys: string[] = [];
  // Padrões: key: "branch" | key: tab === "tes" ? "a" : "b" | key: tab === "tes" ? "a" : tab === "cte" ? "b" : "c"
  for (const col of block.split(/\{\s*key:/).slice(1)) {
    if (!/sortable:\s*true/.test(col)) continue;
    const triple = col.match(
      /^\s*tab === "tes" \? "([^"]+)" : tab === "cte" \? "([^"]+)" : "([^"]+)"/,
    );
    if (triple) {
      keys.push(
        tab === "tes" ? triple[1] : tab === "cte" ? triple[2] : triple[3],
      );
      continue;
    }
    const dual = col.match(/^\s*tab === "tes" \? "([^"]+)" : "([^"]+)"/);
    if (dual) {
      keys.push(tab === "tes" ? dual[1] : dual[2]);
      continue;
    }
    const plain = col.match(/^\s*"([^"]+)"/);
    if (plain) keys.push(plain[1]);
  }
  return keys;
}

describe("U12 R2 sort contract MFE ⊆ BFF por aba", () => {
  it("ocorrências sortable ⊆ OCCURRENCE_SORT_WHITELIST", () => {
    const source = readFileSync(ANALYSIS_PAGE, "utf8");
    const keys = extractOccurrenceSortKeys(source);
    expect(keys.length).toBeGreaterThan(0);
    for (const key of keys) {
      expect(
        WHITELIST_BY_RESOURCE.occurrences.has(key),
        `occurrences: "${key}" fora da whitelist`,
      ).toBe(true);
    }
  });

  it("cada aba genérica só emite chaves da whitelist do recurso", () => {
    const source = readFileSync(ANALYSIS_PAGE, "utf8");
    for (const tabDef of ENTRY_AUDIT_TABS) {
      if (tabDef.value === "occurrences") continue;
      const resource =
        tabDef.value === "tes"
          ? "tes"
          : tabDef.value === "cte"
            ? "cte"
            : tabDef.value === "unmatched"
              ? "unmatched"
              : "documents";
      const whitelist = WHITELIST_BY_RESOURCE[resource];
      const keys = resolveGenericKeysForTab(source, tabDef.value);
      expect(keys.length, `${tabDef.value} sem sortable`).toBeGreaterThan(0);
      for (const key of keys) {
        expect(
          whitelist.has(key),
          `${tabDef.value} (${resource}): "${key}" fora da whitelist`,
        ).toBe(true);
      }
    }
  });

  it("troca de aba zera sort/order na URL (OC-2)", () => {
    const source = readFileSync(ANALYSIS_PAGE, "utf8");
    expect(source).toMatch(
      /navigateWith\(\{\s*tab: item\.value,\s*sort: "",\s*order: "",\s*page: "1",\s*\}\)/,
    );
    expect(entryAuditTabResource("posted_outside")).toBe("documents");
  });
});
