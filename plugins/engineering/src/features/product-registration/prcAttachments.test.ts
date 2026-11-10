import { describe, expect, it } from "vitest";

import {
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_BYTES,
  PRC_ATTACHMENT_STATE_LABELS,
  prcCheckAttachmentFile,
  prcFormatSize,
} from "./prcAttachments";

const mk = (name: string, size = 100, type = "application/pdf"): File =>
  new File([new Uint8Array(size)], name, { type });

describe("PRC-REF-023 — prcCheckAttachmentFile", () => {
  it("aceita PDF válido", () => {
    expect(prcCheckAttachmentFile(mk("spec.pdf")).ok).toBe(true);
  });
  it("aceita imagens permitidas", () => {
    for (const n of ["f.png", "f.jpg", "f.jpeg", "f.webp"]) {
      expect(prcCheckAttachmentFile(mk(n, 10, "image/png")).ok).toBe(true);
    }
  });
  it("rejeita extensão não permitida", () => {
    const r = prcCheckAttachmentFile(mk("evil.exe"));
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.error).toContain("Tipo não permitido");
  });
  it("rejeita vazio e acima do limite", () => {
    expect(prcCheckAttachmentFile(mk("a.pdf", 0)).ok).toBe(false);
    expect(
      prcCheckAttachmentFile(mk("a.pdf", PRC_ATTACHMENT_MAX_BYTES + 1)).ok,
    ).toBe(false);
  });
  it("accept cobre os 4 tipos do contrato", () => {
    expect(PRC_ATTACHMENT_ACCEPT).toBe(".pdf,.png,.jpg,.jpeg,.webp");
  });
  it("formatSize formata B/KB/MB", () => {
    expect(prcFormatSize(500)).toBe("500 B");
    expect(prcFormatSize(2048)).toBe("2 KB");
    expect(prcFormatSize(10 * 1024 * 1024)).toBe("10.0 MB");
  });
  it("estados documentais rotulados", () => {
    expect(PRC_ATTACHMENT_STATE_LABELS.AVAILABLE).toBe("Disponível");
    expect(PRC_ATTACHMENT_STATE_LABELS.PENDING_SCAN).toBe("Em análise");
  });
});
