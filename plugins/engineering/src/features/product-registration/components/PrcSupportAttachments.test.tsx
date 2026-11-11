/** PRC-REF-023 — asserções de fonte: upload usa primitivas oficiais
 * plugin-ui via façade engineeringUi (dropzone + strip + modal). */

import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const src = (rel: string) => readFileSync(resolve(__dirname, rel), "utf8");
const createPage = () => src("../pages/PrcCreatePage.tsx");
const detailSection = () => src("./PrcAttachmentsSection.tsx");
const facade = () => src("../../../ui/engineeringUi.ts");

describe("PRC-REF-023 — upload via plugin-ui oficial", () => {
  it("FileDropzone oficial renderizado na seção de documentos", () => {
    const t = createPage();
    expect(t).toContain("EngineeringFileDropzone");
    expect(t).toContain('title="Documentos de apoio (opcional)"');
  });
  it("não há input file nativo visível na página", () => {
    expect(createPage()).not.toMatch(/<input[^>]*type="file"/);
  });
  it("accept e limites derivam da política compartilhada", () => {
    const t = createPage();
    expect(t).toContain("accept={PRC_ATTACHMENT_ACCEPT}");
    expect(t).toContain("PRC_ATTACHMENT_MAX_COUNT");
    expect(t).toContain("PRC_ATTACHMENT_MAX_MB");
  });
  it("MFE não importa componentes internos do my-requests", () => {
    const t = createPage();
    expect(t).not.toContain("my-requests");
    expect(t).not.toContain("StagedAttachmentsField");
    expect(t).not.toContain("mrUi");
  });
});

describe("PRC-REF-023-FIX-02 — miniaturas e modal de prévia", () => {
  it("PreviewStrip oficial substitui a lista vertical (create)", () => {
    const t = createPage();
    expect(t).toContain("EngineeringAttachmentPreviewStrip");
    expect(t).toContain('mode="manage"');
    expect(t).not.toContain("EngineeringAttachmentFileList");
  });
  it("modal FilePreviewModal com arquivo local (create)", () => {
    const t = createPage();
    expect(t).toContain("EngineeringFilePreviewModal");
    expect(t).toContain("source={previewFile}");
    expect(t).toContain('"Ainda não enviado"');
  });
  it("PreviewStrip + modal no detalhe com fetch autenticado lazy", () => {
    const t = detailSection();
    expect(t).toContain("EngineeringAttachmentPreviewStrip");
    expect(t).toContain('mode="preview"');
    expect(t).toContain("EngineeringFilePreviewModal");
    // blob só via endpoint autenticado — nunca URL pública/storageKey
    expect(t).toContain("downloadPrcAttachment");
    expect(t).not.toContain("storageKey");
    expect(t).not.toMatch(/storage_key/i);
  });
  it("object URLs de miniaturas locais são revogadas", () => {
    const t = createPage();
    expect(t).toContain("URL.createObjectURL(f)");
    expect(t).toContain("URL.revokeObjectURL(url)");
    // cleanup do effect com a memo como dep
    expect(t).toMatch(/thumbUrls\.forEach\(\(url\)\s*=>\s*URL\.revokeObjectURL/);
  });
  it("object URLs de thumbs persistidas são revogadas", () => {
    const t = detailSection();
    expect(t).toContain("URL.createObjectURL(blob)");
    expect(t).toMatch(/Object\.values\(created\)\.forEach\(\(u\)\s*=>\s*URL\.revokeObjectURL/);
  });
  it("estados por arquivo: selecionado/enviando/enviado/erro", () => {
    const t = createPage();
    expect(t).toContain('"Selecionado"');
    expect(t).toContain('"Enviando…"');
    expect(t).toContain('"Enviado"');
    expect(t).toContain("`Erro — ${fileErrors[f.localId]}`");
  });
  it("retry envia só documentos não confirmados (uploadedIds)", () => {
    const t = createPage();
    expect(t).toContain("uploadedIds.has(entry.localId)");
    expect(t).toContain("Tentar enviar documentos novamente");
    // create só ocorre quando createdRequestId é nulo
    expect(t).toMatch(/createdRequestId\s*\?\s*null\s*:\s*await prcIntakeSubmit/);
  });
  it("download autorizado por ação explícita (detalhe + modal)", () => {
    const t = detailSection();
    expect(t).toContain('variant="ghost"');
    expect(t).toContain("Baixar");
    expect(t).toMatch(/a\.download\s*=\s*att\.originalFileName/);
  });
  it("façade exporta wrappers das primitivas de preview", () => {
    const f = facade();
    expect(f).toContain("createDashboardAttachmentPreviewStrip");
    expect(f).toContain("attachmentPreviewStripBemClasses(ENG_UI_PREFIX)");
    expect(f).toContain("FilePreviewModal");
    expect(f).toContain("portalScopeClassName: ENG_PORTAL_SCOPE");
  });
});
