import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const preview = readFileSync(
  join(root, "components/process/ProcessBpmnPreview.tsx"),
  "utf8",
);
const card = readFileSync(
  join(root, "components/process/ProcessBpmnCard.tsx"),
  "utf8",
);
const page = readFileSync(
  join(root, "ui/pages/ProcessDetailPage.tsx"),
  "utf8",
);

describe("G9 — prévia read-only do BPMN nativo no card do processo", () => {
  it("thumbnail deriva do working copy via renderer compartilhado", () => {
    expect(preview).toMatch(/fetchProcessBpmnWorkingCopy\(processoId/);
    expect(preview).toMatch(/renderBpmnThumbnail/);
    expect(preview).toMatch(/@delpi\/bpmn-editor/);
  });

  it("cobre estados loading / empty / error / svg", () => {
    expect(preview).toMatch(/kind: "loading"/);
    expect(preview).toMatch(/kind: "empty"/);
    expect(preview).toMatch(/kind: "error"/);
    expect(preview).toMatch(/Gerando prévia do diagrama/);
    expect(preview).toMatch(/ainda não tem elementos/);
    expect(preview).toMatch(/Não foi possível renderizar/);
  });

  it("ações Ver prévia / Tela cheia / Editar diagrama", () => {
    expect(preview).toMatch(/Ver prévia/);
    expect(preview).toMatch(/Tela cheia/);
    expect(preview).toMatch(/Editar diagrama/);
    expect(preview).toMatch(/buildProcessoBpmnEditPath\(processoId\)/);
    // lightbox read-only, dois níveis (wide + page)
    expect(preview).toMatch(/WideModal/);
    expect(preview).toMatch(/HostContainedPageDialog/);
    expect(preview).toMatch(/Visualização somente leitura/);
  });

  it("metadados: processo, working copy, sha, atualização", () => {
    expect(preview).toMatch(/processName/);
    expect(preview).toMatch(/working copy/);
    expect(preview).toMatch(/document\.version/);
    expect(preview).toMatch(/working_copy_sha256\.slice/);
    expect(preview).toMatch(/updated_at/);
  });

  it("read-only puro — nenhum write/persistência paralela", () => {
    expect(preview).not.toMatch(/saveProcessBpmn|createProcessBpmn|deleteProcessBpmn|fetch\(.*PUT|method: "POST"/);
    expect(preview).not.toMatch(/bpmn-modeler-api|bpmn_modeler/);
  });

  it("preview invalida por sha do working copy (re-render pós-save)", () => {
    expect(preview).toMatch(/document\.working_copy_sha256/);
  });

  it("card renderiza a prévia apenas com documento nativo", () => {
    expect(card).toMatch(/<ProcessBpmnPreview/);
    expect(card).toMatch(/document \? \(/);
    // empty state continua cobrindo processo sem BPMN
    expect(card).toMatch(/Criar diagrama BPMN/);
    expect(card).toMatch(/ProcessBpmnReferenceCard/);
  });

  it("página passa o nome do processo como metadado", () => {
    expect(page).toMatch(/processName=\{processo\.nome_processo\}/);
  });
});
