import { describe, expect, it } from "vitest";

import { PRC_ATTACHMENT_MAX_COUNT } from "./prcAttachments";
import {
  addSupportFiles,
  newSupportFileId,
  removeSupportFile,
  type PrcSupportFile,
} from "./prcSupportFiles";

const mk = (name: string, size = 100, type = "application/pdf"): File =>
  new File([new Uint8Array(size)], name, { type });

const ids = (files: PrcSupportFile[]) => files.map((f) => f.localId);

describe("PRC-REF-023-F02 — identidade estável de arquivos", () => {
  it("gera ids únicos mesmo para arquivos homônimos", () => {
    const a = newSupportFileId(mk("spec.pdf"));
    const b = newSupportFileId(mk("spec.pdf"));
    expect(a).not.toBe(b);
  });

  it("remover pendente anterior preserva identidade dos demais", () => {
    const { files } = addSupportFiles(
      [],
      [mk("a.pdf"), mk("b.pdf"), mk("c.pdf")],
      PRC_ATTACHMENT_MAX_COUNT,
    );
    const [first, second, third] = files;
    const after = removeSupportFile(files, first.localId);
    expect(ids(after)).toEqual([second.localId, third.localId]);
    // O localId do irmão não muda — estado enviado/erro nunca desliza.
    expect(after[0].file.name).toBe("b.pdf");
    expect(after[0].localId).toBe(second.localId);
  });

  it("novas seleções preservam ids já existentes", () => {
    const first = addSupportFiles(
      [],
      [mk("a.pdf")],
      PRC_ATTACHMENT_MAX_COUNT,
    );
    const second = addSupportFiles(
      first.files,
      [mk("b.pdf")],
      PRC_ATTACHMENT_MAX_COUNT,
    );
    expect(second.files[0].localId).toBe(first.files[0].localId);
    expect(second.files).toHaveLength(2);
  });

  it("erros de validação são indexados por localId, não por posição", () => {
    const { files, errors } = addSupportFiles(
      [],
      [mk("ok.pdf"), mk("evil.exe")],
      PRC_ATTACHMENT_MAX_COUNT,
    );
    expect(files).toHaveLength(1);
    const errorIds = Object.keys(errors);
    expect(errorIds).toHaveLength(1);
    // Erro não pode colidir com o id do arquivo aceito.
    expect(errorIds[0]).not.toBe(files[0].localId);
    expect(errorIds[0]).toContain("evil.exe");
  });

  it("respeita o limite máximo sem reatribuir ids", () => {
    const base = Array.from({ length: PRC_ATTACHMENT_MAX_COUNT }, (_, i) =>
      mk(`f${i}.pdf`),
    );
    const full = addSupportFiles([], base, PRC_ATTACHMENT_MAX_COUNT);
    const extra = addSupportFiles(
      full.files,
      [mk("extra.pdf")],
      PRC_ATTACHMENT_MAX_COUNT,
    );
    expect(extra.files).toHaveLength(PRC_ATTACHMENT_MAX_COUNT);
    expect(ids(extra.files)).toEqual(ids(full.files));
  });
});
