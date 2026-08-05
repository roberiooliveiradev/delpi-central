import { describe, expect, it } from "vitest";
import { validateClientUpload } from "./documentUpload";

describe("validateClientUpload", () => {
  it("rejeita ausência de arquivo", () => {
    expect(validateClientUpload(null).ok).toBe(false);
  });

  it("aceita PDF válido", () => {
    const file = new File([new Uint8Array([1, 2, 3])], "carta.pdf", {
      type: "application/pdf",
    });
    expect(validateClientUpload(file)).toEqual({ ok: true });
  });

  it("rejeita extensão inválida", () => {
    const file = new File([new Uint8Array([1])], "malware.exe", {
      type: "application/octet-stream",
    });
    const result = validateClientUpload(file);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toMatch(/Extensão/i);
    }
  });

  it("rejeita arquivo acima do limite", () => {
    const huge = new Uint8Array(26 * 1024 * 1024);
    const file = new File([huge], "big.pdf", { type: "application/pdf" });
    const result = validateClientUpload(file);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.message).toMatch(/25 MB/i);
    }
  });
});
