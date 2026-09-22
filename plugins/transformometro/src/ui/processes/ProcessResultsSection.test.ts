import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(join(root, "ui/processes/ProcessResultsSection.tsx"), "utf8");

describe("ProcessResultsSection", () => {
  it("CASE C/T: múltiplas instâncias exigem seleção explícita e não usam instances[0]", () => {
    expect(source).toMatch(/requiresInstanceSelection/);
    expect(source).toMatch(/Selecione uma melhoria para visualizar este conteúdo/);
    expect(source).not.toMatch(/instancias\[0\].*requiresInstanceSelection|selectedInstanciaId\s*=\s*instancias\[0\]/);
    expect(source).toMatch(/if \(instancias\.length === 1\) return instancias\[0\]/);
    expect(source).toMatch(/if \(requiresInstanceSelection\) return selectedInstanciaId/);
    expect(source).toMatch(/data-selected-instancia=\{contextInstanciaId\}/);
  });

  it("CASE T: baseline e scenario da mesma composição usam um único contextInstanciaId", () => {
    expect(source).toMatch(/const contextInstanciaId = resolvedInstanciaId/);
    expect(source).toMatch(
      /buildProcessoPath\(processoId, revisao\.revisao_id, contextInstanciaId\)/,
    );
  });

  it("CASE F/G/U: comparação é section-triggered e rotula calculado", () => {
    expect(source).toMatch(/if \(!active\) return/);
    expect(source).toMatch(/fetchProcessoComparativo/);
    expect(source).toMatch(/Comparação \(calculado\)/);
    expect(source).toMatch(/Ainda não há baseline\/medição comparável/);
  });

  it("CASE A: empty de melhorias sem inventar Improvement entity", () => {
    expect(source).toMatch(/Nenhuma melhoria operacional registrada/);
    expect(source).not.toMatch(/Improvement/);
  });
});
