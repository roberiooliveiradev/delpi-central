import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");

const section = readFileSync(
  join(root, "ui/revision/registration/RevisionDiagnosticSection.tsx"),
  "utf8",
);
const content = readFileSync(
  join(root, "ui/revision/diagnostic/DiagnosticContent.tsx"),
  "utf8",
);
const panel = readFileSync(
  join(root, "ui/revision/diagnostic/DiagnosticActionPanel.tsx"),
  "utf8",
);
const nav = readFileSync(join(root, "ui/processes/processWorkspaceNav.ts"), "utf8");
const page = readFileSync(join(root, "ui/pages/RevisionRegistrationPanel.tsx"), "utf8");
const app = readFileSync(join(root, "App.tsx"), "utf8");

describe("Revision Diagnostic — wiring", () => {
  it("registra Diagnóstico como seção da revisão (não página root)", () => {
    expect(nav).toMatch(/id:\s*"diagnostico",\s*label:\s*"Diagnóstico"/);
    expect(page).toMatch(/RevisionDiagnosticSection/);
    expect(page).toMatch(/sectionId="diagnostico"/);
    expect(app).not.toMatch(/\/diagnostics/);
    expect(app).not.toMatch(/DiagnosticosPage|DiagnosticsPage/i);
  });

  it("deep link canônico #diagnostico/{id} com validação de pertencimento", () => {
    expect(nav).toMatch(/parseRevisaoDiagnosticIdFromHash/);
    expect(nav).toMatch(/buildRevisaoDiagnosticHref/);
    // Mismatch Revision → estado explícito, nunca seleção silenciosa.
    expect(section).toMatch(/mismatch/);
    expect(section).toMatch(/ctx\.diagnostic\.revision_id !== revisaoId/);
  });
});

describe("Revision Diagnostic — semântica canônica", () => {
  it("Problema investigado é read-only (sem edição/exclusão)", () => {
    expect(content).toMatch(/Problema investigado/);
    expect(content).not.toMatch(/edit[a-z_]*\s*problem|onEdit.*statement/i);
    // Nenhuma action material edita o statement pós-criação.
    expect(content).not.toMatch(/edit_problem|delete_problem|update_problem/);
  });

  it("achados mostram natureza epistêmica separada do papel", () => {
    expect(content).toMatch(/epistemicLabel\(f\.epistemic_state\)/);
    expect(content).toMatch(/Papel:\s*\$\{FINDING_ROLE_LABELS/);
  });

  it("hipóteses mostram INFERRED separado do lifecycle", () => {
    // Badge epistêmico (Inferido) e badge de status (lifecycle) são dois badges.
    expect(content).toMatch(/epistemicLabel\(h\.epistemic_state \?\? "INFERRED"\)/);
    expect(content).toMatch(/Status:\s*\$\{lifecycleLabel\(h\.lifecycle\)\}/);
    // VALIDATED nunca vira "fato".
    expect(content).not.toMatch(/fato confirmado|confirmado como fato|verified/i);
  });

  it("causal usa somente CONTRIBUTES_TO (copy «contribui para»)", () => {
    expect(content).toMatch(/CAUSAL_RELATION_LABEL/);
    expect(panel).toMatch(/CAUSAL_RELATION_LABEL/);
    // O payload causal carrega só origem/destino — nunca um relation livre.
    expect(panel).toMatch(
      /case "add_causal_link":[\s\S]*?return \{\s*source_hypothesis_id: draft\.source_hypothesis_id,\s*target_id: draft\.target_id,\s*\}/,
    );
  });

  it("CONTRADICTS é first-class com label textual «Contradiz»", () => {
    expect(content).toMatch(/CONTRADICTS/);
    expect(content).toMatch(/tm-diagnostic-evidence--contradicts/);
  });

  it("conclusão mostra INFERRED + lifecycle + validação efetiva simultâneos", () => {
    expect(content).toMatch(/epistemicLabel\(c\.epistemic_state \?\? "INFERRED"\)/);
    expect(content).toMatch(/Status:\s*\$\{lifecycleLabel\(c\.lifecycle\)\}/);
    expect(content).toMatch(/EffectiveBadge value=\{c\.effective_validation/);
    expect(content).toMatch(/Causa-raiz apontada/);
  });

  it("status de validação efetiva cobre os três estados canônicos", () => {
    expect(content).toMatch(/REVALIDATION_REQUIRED/);
    expect(content).toMatch(/STALE_EVIDENCE/);
  });

  it("não existe editar/remover/desvincular genérico", () => {
    for (const source of [section, content, panel]) {
      expect(source).not.toMatch(/remove_finding|edit_finding|delete_finding/);
      expect(source).not.toMatch(/remove_hypothesis|edit_hypothesis|delete_hypothesis/);
      expect(source).not.toMatch(/remove_evidence_link|unlink/);
      expect(source).not.toMatch(/edit_conclusion|delete_conclusion|remove_conclusion/);
    }
  });
});

describe("Revision Diagnostic — fluxo governado", () => {
  it("PREPARE → revisão de exact_change → confirmação explícita → COMMIT → read-back", () => {
    expect(panel).toMatch(/prepareManageDiagnostic/);
    expect(panel).toMatch(/Revise a alteração preparada/);
    expect(panel).toMatch(/exact_change/);
    expect(panel).toMatch(/commitGovernedProposal/);
    // COMMIT 2xx não é sucesso: verificação via GET canônico.
    expect(panel).toMatch(/verifyDiagnosticOutcome/);
    expect(panel).toMatch(/fetchDiagnostic/);
    expect(panel).toMatch(/OUTCOME_VERIFICATION_FAILED/);
  });

  it("create segue o mesmo fluxo governado", () => {
    expect(section).toMatch(/prepareCreateDiagnostic/);
    expect(section).toMatch(/commitGovernedProposal/);
    expect(section).toMatch(/Revise a alteração preparada/);
    // Verificação de read-back na lista canônica antes do sucesso.
    expect(section).toMatch(/confirmed/);
  });

  it("proposal stale/concorrência bloqueia confirmação com copy canônica", () => {
    const copy =
      "Este diagnóstico foi alterado desde a preparação da mudança";
    expect(section).toContain(copy);
    expect(panel).toContain(copy);
  });

  it("sem endpoints paralelos — somente o cliente canônico", () => {
    for (const source of [section, content, panel]) {
      expect(source).not.toMatch(/fetch\(\s*["'`]\$\{?TRANSFORMOMETRO_API_BASE/);
      expect(source).not.toMatch(/supabase|\.from\(/);
    }
  });
});

describe("Revision Diagnostic — realtime", () => {
  it("assina a sala canônica da revisão (não cria websocket novo)", () => {
    expect(section).toMatch(/useTransformometroEntityWatch/);
    expect(section).toMatch(/entityType:\s*"revisao"/);
    expect(section).not.toMatch(/new WebSocket/);
  });

  it("anti-eco via actorClientId existente", () => {
    expect(section).toMatch(/getTransformometroClientId/);
  });

  it("conflito local não sobrescreve estado e não auto-merja", () => {
    expect(section).toMatch(/local-conflict/);
    expect(section).toMatch(/Este diagnóstico foi atualizado em outro local/);
    expect(section).not.toMatch(/auto.?merge|mergeRemote/i);
  });
});

describe("Revision Diagnostic — acessibilidade/estados", () => {
  it("headings semânticos e aria nos blocos", () => {
    expect(content).toMatch(/aria-labelledby="tm-diag-problem"/);
    expect(content).toMatch(/aria-labelledby="tm-diag-findings"/);
    expect(content).toMatch(/aria-labelledby="tm-diag-hypotheses"/);
    expect(content).toMatch(/aria-labelledby="tm-diag-causal"/);
    expect(content).toMatch(/aria-labelledby="tm-diag-evidence"/);
    expect(content).toMatch(/aria-labelledby="tm-diag-conclusion"/);
  });

  it("estados vazio/erro/forbidden/não encontrado separados", () => {
    expect(section).toMatch(/Nenhum diagnóstico registrado nesta revisão/);
    expect(section).toMatch(/Iniciar diagnóstico/);
    expect(section).toMatch(/not_found/);
    expect(section).toMatch(/forbidden/);
    expect(section).toMatch(/detailState === "error"/);
  });

  it("múltiplos diagnósticos têm seletor explícito (sem rótulo «principal/atual»)", () => {
    expect(section).toMatch(/tm-diagnostic-selector/);
    // Nenhum label renderizado como Principal/Atual/Padrão/Corrente.
    expect(section + content).not.toMatch(
      />\s*(Principal|Atual|Padrão|Corrente)\b/,
    );
  });

  it("foco gerenciado após PREPARE e após resultado", () => {
    expect(panel).toMatch(/reviewHeadingRef/);
    expect(panel).toMatch(/reviewHeadingRef\.current\.focus\(\)/);
    expect(section).toMatch(/successRef\.current\.focus\(\)/);
  });
});
