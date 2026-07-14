/**
 * Regressão: campos usados na busca da lista (responsável + auditores).
 * Mantém o mesmo haystack de `filterAuditList` em auditList.ts.
 * Uso: node --experimental-strip-types scripts/check-audit-list-search.ts
 */
import assert from "node:assert/strict";

type Item = {
  audit_code: string;
  area_name: string;
  area_responsible: string;
  auditor_names?: string | null;
  shift: string;
};

function matchesSearch(item: Item, rawSearch: string): boolean {
  const search = rawSearch.trim().toLowerCase();
  if (!search) return true;
  const haystack = [
    item.audit_code,
    item.area_name,
    item.area_responsible,
    item.auditor_names ?? "",
    item.shift,
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(search);
}

const item: Item = {
  audit_code: "01-000001",
  area_name: "Montagem",
  area_responsible: "Maria Silva",
  auditor_names: "João Souza, Ana Costa",
  shift: "TURNO_1",
};

assert.equal(matchesSearch(item, "maria"), true);
assert.equal(matchesSearch(item, "MARIA SILVA"), true);
assert.equal(matchesSearch(item, "joão"), true);
assert.equal(matchesSearch(item, "ANA costa"), true);
assert.equal(matchesSearch(item, "pedro"), false);

console.log("ok: busca por responsável e auditor (case-insensitive)");
