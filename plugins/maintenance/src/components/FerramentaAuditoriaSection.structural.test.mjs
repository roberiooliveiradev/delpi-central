#!/usr/bin/env node
/**
 * Helpdesk #1488: a auditoria da ferramenta deve ocupar pouco espaço quando recolhida.
 * O colapso é implementado pelo SectionCard canônico (com cobertura de UI no plugin-ui).
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "FerramentaAuditoriaSection.tsx"), "utf8");

describe("FerramentaAuditoriaSection — #1488", () => {
  it("permite minimizar e expandir por controle acessivel no titulo", () => {
    assert.match(source, /const \[auditoriaOpen, setAuditoriaOpen\] = useState\(true\)/);
    assert.match(source, /<SectionCard[\s\S]*?\bcollapsible\s+open=\{auditoriaOpen\}\s+onOpenChange=\{setAuditoriaOpen\}/);
    assert.match(source, /collapseAriaLabel:/);
    assert.match(source, /expandAriaLabel:/);
  });

  it("oculta controles da linha do tempo mas preserva o contador ao recolher", () => {
    assert.match(source, /\{auditoriaOpen \? \(\s*<div\s+className="dm-view-toggle"/);
    assert.match(source, /\) : null\}\s*<span className="dm-badge">\{total\} evento\(s\)<\/span>/);
  });

  it("preserva estado e consulta da auditoria na mesma instancia", () => {
    assert.match(source, /useState<AuditoriaViewMode>\("timeline"\)/);
    assert.match(source, /const auditTable = useServerTable\(\{ pageSize: 10 \}\)/);
    assert.match(source, /fetchFerramentaAuditoria\(/);
  });
});
