import { describe, expect, it } from "vitest";
import {
  attachmentTypeLabel,
  mapCapexAttachmentError,
  newAttachmentIdempotencyKey,
  uploadStatusLabel,
  validateAttachmentUploadForm,
} from "./capexAttachments";
import { HttpRequestError } from "../api/httpClient";

describe("capexAttachments utils", () => {
  it("labels de tipo alinhados ao backend", () => {
    expect(attachmentTypeLabel("quotation")).toBe("Orçamento");
    expect(attachmentTypeLabel("commercial_proposal")).toBe("Proposta comercial");
    expect(attachmentTypeLabel("technical_specification")).toBe("Especificação técnica");
    expect(attachmentTypeLabel("image")).toBe("Imagem");
    expect(attachmentTypeLabel("justification")).toBe("Justificativa");
    expect(attachmentTypeLabel("other")).toBe("Outro documento");
  });

  it("valida nome, tipo e arquivo", () => {
    const file = new File([new Uint8Array([1])], "a.pdf", { type: "application/pdf" });
    expect(
      validateAttachmentUploadForm({ file: null, displayName: "X", attachmentType: "other" }).ok,
    ).toBe(false);
    expect(
      validateAttachmentUploadForm({ file, displayName: "", attachmentType: "other" }).ok,
    ).toBe(false);
    expect(
      validateAttachmentUploadForm({ file, displayName: "X", attachmentType: "" }).ok,
    ).toBe(false);
    expect(
      validateAttachmentUploadForm({ file, displayName: "X", attachmentType: "other" }),
    ).toEqual({ ok: true });
  });

  it("rejeita arquivo acima de 25 MB", () => {
    const huge = new File([new Uint8Array(26 * 1024 * 1024)], "big.pdf", {
      type: "application/pdf",
    });
    const result = validateAttachmentUploadForm({
      file: huge,
      displayName: "Big",
      attachmentType: "other",
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toMatch(/25 MB/i);
  });

  it("mapeia erros de MIME, extensão e tamanho", () => {
    expect(
      mapCapexAttachmentError(
        new HttpRequestError("[budget_capex_attachment_mime_invalid] x", 422),
      ),
    ).toMatch(/MIME/i);
    expect(
      mapCapexAttachmentError(
        new HttpRequestError("[budget_capex_attachment_extension_invalid] x", 422),
      ),
    ).toMatch(/extensão/i);
    expect(
      mapCapexAttachmentError(
        new HttpRequestError("[budget_capex_attachment_too_large] x", 422),
      ),
    ).toMatch(/25 MB/i);
  });

  it("mapeia 401 e 403", () => {
    expect(mapCapexAttachmentError(new HttpRequestError("x", 401))).toMatch(/Sessão expirada/i);
    expect(mapCapexAttachmentError(new HttpRequestError("x", 403))).toMatch(/Acesso negado/i);
  });

  it("gera idempotency keys distintas", () => {
    const a = newAttachmentIdempotencyKey();
    const b = newAttachmentIdempotencyKey();
    expect(a).not.toBe(b);
    expect(a.length).toBeGreaterThan(8);
  });

  it("rótulos de progresso", () => {
    expect(uploadStatusLabel("ready")).toBe("Pronto para enviar");
    expect(uploadStatusLabel("uploading")).toBe("Enviando");
    expect(uploadStatusLabel("processing")).toBe("Processando");
    expect(uploadStatusLabel("done")).toBe("Concluído");
    expect(uploadStatusLabel("error")).toBe("Erro no envio");
  });
});
