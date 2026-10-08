import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("G5 — referência explícita processo ↔ BPMN Modeler", () => {
  it("deep links usam as rotas product-owned do Modelador", () => {
    const api = readFileSync(join(root, "data/api/bpmnReferenceApi.ts"), "utf8");
    expect(api).toMatch(/\/apps\/bpmn-modeler\/models\/\$\{modelId\}\/revisions\/\$\{revisionNumber\}/);
    expect(api).toMatch(/\/apps\/bpmn-modeler\/models\/\$\{modelId\}/);
    expect(api).not.toMatch(/http:\/\/localhost/);
    expect(api).not.toMatch(/https:\/\/localhost/);
  });

  it("card cobre estados empty / resolved / unavailable / inaccessible", () => {
    const card = readFileSync(
      join(root, "components/process/ProcessBpmnReferenceCard.tsx"),
      "utf8"
    );
    expect(card).toMatch(/Nenhum modelo BPMN vinculado/);
    expect(card).toMatch(/Vincular modelo BPMN/);
    expect(card).toMatch(/temporariamente indisponível/);
    expect(card).toMatch(/sem acesso ou não encontrada/);
    expect(card).toMatch(/Visualizar revisão/);
    expect(card).toMatch(/Abrir no Modelador/);
    expect(card).toMatch(/Desvincular/);
  });

  it("não segue latest automaticamente — badge é read-only", () => {
    const card = readFileSync(
      join(root, "components/process/ProcessBpmnReferenceCard.tsx"),
      "utf8"
    );
    expect(card).toMatch(/latest_revision_number > reference\.revision_number/);
    expect(card).toMatch(/Existe uma revisão BPMN mais recente/);
    // write só no handler de confirmação explícita do picker
    expect(card).toMatch(/handleConfirm[\s\S]*setProcessBpmnReference/);
  });

  it("unlink confirma que não exclui o modelo BPMN", () => {
    const card = readFileSync(
      join(root, "components/process/ProcessBpmnReferenceCard.tsx"),
      "utf8"
    );
    expect(card).toMatch(/Desvincular não excluirá o modelo BPMN/);
  });

  it("picker exige revisão explícita e bloqueia modelo sem revisão", () => {
    const card = readFileSync(
      join(root, "components/process/ProcessBpmnReferenceCard.tsx"),
      "utf8"
    );
    expect(card).toMatch(/Este modelo ainda não possui uma revisão/);
    expect(card).toMatch(/disabled=\{noRevision\}/);
    expect(card).toMatch(/selectedRevision != null/);
  });

  it("página de processo monta o card na subseção Fluxo", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
    expect(page).toMatch(/ProcessBpmnReferenceCard/);
    const fluxo = page.indexOf('data-subsection="fluxo"');
    const cardIdx = page.indexOf("ProcessBpmnReferenceCard", fluxo);
    expect(cardIdx).toBeGreaterThan(fluxo);
  });
});
