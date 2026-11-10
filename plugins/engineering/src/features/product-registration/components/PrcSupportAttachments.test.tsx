/** PRC-REF-023-F01-FIX-01 — o upload usa o kit oficial @delpi/plugin-ui
 * via façade engineeringUi; input nativo visível não pode retornar. */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const src = (rel: string) =>
  readFileSync(resolve(__dirname, rel), "utf8");

const createPage = () => src("../pages/PrcCreatePage.tsx");
const facade = () => src("../../../ui/engineeringUi.ts");

describe("PRC-REF-023-F01-FIX-01 — upload via plugin-ui oficial", () => {
  it("FileDropzone oficial renderizado na seção de documentos", () => {
    const t = createPage();
    expect(t).toContain("EngineeringFileDropzone");
    expect(t).toContain("EngineeringAttachmentFileList");
    expect(t).toContain('title="Documentos de apoio (opcional)"');
  });
  it("não há input file nativo visível na página", () => {
    expect(createPage()).not.toMatch(/<input[^>]*type="file"/);
  });
  it("dropzone usa input oculto do kit (hideInput)", () => {
    expect(createPage()).toContain("hideInput");
  });
  it("accept vem da política compartilhada (não string solta)", () => {
    const t = createPage();
    expect(t).toContain("accept={PRC_ATTACHMENT_ACCEPT}");
    expect(t).toContain("PRC_ATTACHMENT_MAX_COUNT");
    expect(t).toContain("PRC_ATTACHMENT_MAX_MB");
  });
  it("arquivos selecionados são marcados como ainda não enviados", () => {
    expect(createPage()).toContain("ainda não enviados");
  });
  it("retry preserva o requestId criado (sem recriar solicitação)", () => {
    const t = createPage();
    expect(t).toContain("createdRequestId");
    expect(t).toContain("Tentar enviar documentos novamente");
    // create só ocorre quando createdRequestId é nulo
    expect(t).toMatch(/createdRequestId\s*\?\s*null\s*:\s*await prcIntakeSubmit/);
  });
  it("façade exporta wrappers com prefixo engineering (BEM dual)", () => {
    const f = facade();
    expect(f).toContain("createDashboardFileDropzone");
    expect(f).toContain('fileDropzoneBemClasses(ENG_UI_PREFIX, "file-dropzone")');
    expect(f).toContain("createDashboardAttachmentFileList");
    expect(f).toContain("attachmentFileListBemClasses(ENG_UI_PREFIX)");
  });
  it("MFE não importa componentes internos do my-requests", () => {
    const t = createPage();
    expect(t).not.toContain("my-requests");
    expect(t).not.toContain("StagedAttachmentsField");
    expect(t).not.toContain("mrUi");
  });
});
