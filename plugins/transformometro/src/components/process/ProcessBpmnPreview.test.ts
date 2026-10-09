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

describe("G9-LAYOUT-1 — prévia live read-only do BPMN nativo no card", () => {
  it("preview é o viewer BPMN real compartilhado — não imagem/snapshot", () => {
    expect(preview).toMatch(/fetchProcessBpmnWorkingCopy\(processoId/);
    expect(preview).toMatch(/BpmnReadonlyViewer/);
    expect(preview).toMatch(/@delpi\/bpmn-editor/);
    // §6/§56: nenhuma imagem estática como experiência primária
    expect(preview).not.toMatch(/renderBpmnThumbnail|<img|dangerouslySetInnerHTML/);
    // pan + wheel zoom + controles +/−/fit — mesmo componente nos 3 mounts
    expect(preview.match(/<BpmnReadonlyViewer[\s>]/g)?.length).toBe(3);
    expect(preview).toMatch(/controls/);
    expect(preview).toMatch(/fitOnLoad/);
  });

  it("cobre estados loading / empty / error via status do viewer", () => {
    expect(preview).toMatch(/kind: "loading"/);
    expect(preview).toMatch(/kind: "error"/);
    expect(preview).toMatch(/status === "empty"/);
    expect(preview).toMatch(/Carregando prévia do diagrama/);
    expect(preview).toMatch(/ainda não tem elementos/);
    expect(preview).toMatch(/Não foi possível renderizar/);
  });

  it("ações Ver prévia / Tela cheia / Editar diagrama", () => {
    expect(preview).toMatch(/Ver prévia/);
    expect(preview).toMatch(/Tela cheia/);
    expect(preview).toMatch(/Editar diagrama/);
    expect(preview).toMatch(/buildProcessoBpmnEditPath\(processoId\)/);
    // lightbox read-only, dois níveis (wide + page) — mesmo viewer
    expect(preview).toMatch(/WideModal/);
    expect(preview).toMatch(/HostContainedPageDialog/);
    expect(preview).toMatch(/Visualização somente leitura/);
  });

  it("metadados: processo, working copy, sha em detalhe técnico (§42)", () => {
    expect(preview).toMatch(/processName/);
    expect(preview).toMatch(/Working copy/);
    expect(preview).toMatch(/document\.version/);
    // checksum sai do texto principal → tooltip/title técnico
    expect(preview).toMatch(/title=\{`Checksum do working copy/);
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
