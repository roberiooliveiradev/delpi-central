import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const source = readFileSync(join(root, "ui/processes/ProcessResultsSection.tsx"), "utf8");
const viewModel = readFileSync(join(root, "ui/processes/buildRevisionComparisonView.ts"), "utf8");
const detailPage = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
const summary = readFileSync(join(root, "ui/processes/RevisionCompareSummary.tsx"), "utf8");
const contextHeader = readFileSync(join(root, "ui/processes/ResultsContextHeader.tsx"), "utf8");
const measurement = readFileSync(join(root, "ui/processes/MeasurementComparisonTable.tsx"), "utf8");
const help = readFileSync(join(root, "content/helpTooltips.ts"), "utf8");

describe("ProcessResultsSection — Redesign & Compare V1 UX polish", () => {
  it("CASE I/T: múltiplas instâncias exigem seleção; um único contexto", () => {
    expect(source).toMatch(/buildRevisionComparisonView/);
    expect(source).toMatch(/Selecione uma melhoria para visualizar este conteúdo/);
    expect(source).toMatch(/data-selected-instancia=\{comparison\.instanceId\}/);
    expect(source).toMatch(/data-reference-revisao=\{comparison\.referenceRevisionId/);
    expect(source).not.toMatch(/instances\[0\]/);
    expect(viewModel).toMatch(/Never invent a fallback/);
  });

  it("CASE H: legacy missing reference explícito (sem fallback)", () => {
    expect(source).toMatch(/legacy_reference_missing/);
    expect(source).toMatch(
      /Este cenário não possui uma referência de comparação definida/,
    );
    expect(viewModel).not.toMatch(/previous revision/);
    expect(viewModel).not.toMatch(/revisoes\[0\]/);
  });

  it("CASE A/B: baseline_only e pair com AS-IS/TO-BE/DELTA hierárquicos", () => {
    expect(source).toMatch(/RevisionCompareSummary/);
    expect(source).toMatch(/baseline_only/);
    expect(source).toMatch(/Ainda não há cenário para comparação/);
    expect(summary).toMatch(/AS-IS/);
    expect(summary).toMatch(/TO-BE/);
    expect(summary).toMatch(/DELTA/);
    expect(summary).toMatch(/Referência atual/);
    expect(summary).toMatch(/Cenário proposto/);
    expect(summary).toMatch(/Diferença calculada/);
  });

  it("CASE D/L/O/P: medição, benefícios calculados e provenance nos headers", () => {
    expect(source).toMatch(/MeasurementComparisonTable/);
    expect(source).toMatch(/Não há indicadores informados para este cenário/);
    expect(source).toMatch(/Benefícios calculados/);
    expect(source).toMatch(/BenefitKpi/);
    expect(source).toMatch(/provenanceForRevisionRole/);
    expect(source).not.toMatch(/BENEFÍCIOS REALIZADOS/);
    expect(source).not.toMatch(/Benefícios obtidos/);
    expect(measurement).toMatch(/AS-IS · INFORMADO/);
    expect(measurement).toMatch(/TO-BE · PROPOSTO/);
    expect(measurement).toMatch(/Δ · CALCULADO/);
    expect(measurement).not.toMatch(/TmStatusBadge/);
    expect(measurement).not.toMatch(/HelpTooltip/);
  });

  it("CASE Q/R: forbidden ≠ empty; erro local", () => {
    expect(source).toMatch(/TransformometroHttpError/);
    expect(source).toMatch(/errorStatus === 403/);
    expect(source).toMatch(/describeHttpErrorTitle/);
    expect(source).toMatch(/revisionErrorStatus === 403/);
  });

  it("CASE S/U: lazy Results + deep link #resultados preservado no workspace", () => {
    expect(source).toMatch(/if \(!active\) return/);
    expect(source).toMatch(/fetchProcessoComparativo/);
    expect(source).toMatch(/showHeavyStructure/);
    expect(detailPage).toMatch(/sectionId="resultados"/);
    const loadMatch = detailPage.match(
      /const load = useCallback\(async \(\) => \{[\s\S]*?\}, \[getAccessToken, processoId\]\);/,
    );
    expect(loadMatch?.[0]).not.toMatch(/fetchProcessoComparativo/);
  });

  it("CASE E/F: impacto no processo sem inventar graph-diff", () => {
    expect(source).toMatch(/Impacto no processo/);
    expect(source).toMatch(/Ver estrutura/);
    expect(source).toMatch(/Ver fluxo/);
    expect(source).not.toMatch(/RedesignAggregate/);
    expect(source).not.toMatch(/RedesignRepository/);
    expect(source).not.toMatch(/graph-diff/);
  });

  it("CASE M/N: investimentos e recursos escopados ao cenário", () => {
    expect(source).toMatch(/Valores necessários para viabilizar o cenário proposto/);
    expect(source).toMatch(/Nenhum investimento registrado para este cenário/);
    expect(source).toMatch(/Nenhum recurso vinculado a este cenário/);
    expect(source).toMatch(/Configurações → Recursos compartilhados/);
  });

  it("UX polish: ordem narrativa, ações explícitas, disclosure detalhada, cenário no contexto", () => {
    expect(contextHeader).toMatch(/Melhoria analisada/);
    expect(contextHeader).toMatch(/Cenário proposto/);
    expect(contextHeader).toMatch(/Referência atual/);
    expect(contextHeader).toMatch(/scenarioPicker/);
    expect(contextHeader).toMatch(/Trocar melhoria/);
    expect(source).toMatch(/scenarioPicker=\{scenarioPicker\}/);
    expect(source).toMatch(/Ver medição/);
    expect(source).toMatch(/Ver investimentos/);
    expect(source).toMatch(/Ver recursos/);
    expect(source).not.toMatch(/Ver na revisão/);
    expect(source).toMatch(/Ver comparação detalhada/);
    expect(source).toMatch(/tm-processo-results-detail-disclosure/);
    expect(source).toMatch(/ResultsProvenanceLegend/);
    expect(source).toMatch(/Indicadores operacionais/);
    expect(source).toMatch(/Benefícios calculados/);
    expect(help).toMatch(/resultados:/);
    expect(source).not.toMatch(/revisao_referencia_id/);
    expect(source).not.toMatch(/contrato de comparação/);

    const indicadoresIdx = source.indexOf('id="medicoes"');
    const beneficiosIdx = source.indexOf('id="beneficios"');
    const investimentosIdx = source.indexOf('id="investimentos"');
    const recursosIdx = source.indexOf('id="recursos"');
    const impactoIdx = source.indexOf('id="estrutura-fluxo"');
    const detalhadaIdx = source.indexOf("Ver comparação detalhada");
    expect(indicadoresIdx).toBeGreaterThan(-1);
    expect(beneficiosIdx).toBeGreaterThan(indicadoresIdx);
    expect(investimentosIdx).toBeGreaterThan(beneficiosIdx);
    expect(recursosIdx).toBeGreaterThan(investimentosIdx);
    expect(impactoIdx).toBeGreaterThan(recursosIdx);
    expect(detalhadaIdx).toBeGreaterThan(impactoIdx);
  });
});
