import { describe, expect, it } from "vitest";

import {
  caretPosAfterDigits,
  digitsBeforePos,
  digitsOnly,
  formatCnpjDigits,
  formatCpfDigits,
  formatTaxIdForPerson,
} from "./taxIdMask";

const CNPJ = "23622391000181";
const CNPJ_MASKED = "23.622.391/0001-81";

describe("digitsOnly", () => {
  it("mantém apenas dígitos e limita a 14 por padrão", () => {
    expect(digitsOnly("abc23622391000181xyz!@#")).toBe(CNPJ);
    expect(digitsOnly("123456789012345678")).toBe("12345678901234");
    expect(digitsOnly("123456789012345678", 11)).toBe("12345678901");
  });

  it("tolerância a null/empty", () => {
    expect(digitsOnly("")).toBe("");
    expect(digitsOnly("-.-/-")).toBe("");
  });
});

describe("formatCnpjDigits — máscara progressiva", () => {
  it("14 dígitos recebem a máscara completa (AC-01)", () => {
    expect(formatCnpjDigits(CNPJ)).toBe(CNPJ_MASKED);
  });

  it("formata progressivamente durante a digitação", () => {
    expect(formatCnpjDigits("")).toBe("");
    expect(formatCnpjDigits("2")).toBe("2");
    expect(formatCnpjDigits("23")).toBe("23");
    expect(formatCnpjDigits("236")).toBe("23.6");
    expect(formatCnpjDigits("23622")).toBe("23.622");
    expect(formatCnpjDigits("236223")).toBe("23.622.3");
    expect(formatCnpjDigits("23622391")).toBe("23.622.391");
    expect(formatCnpjDigits("236223910")).toBe("23.622.391/0");
    expect(formatCnpjDigits("236223910001")).toBe("23.622.391/0001");
    expect(formatCnpjDigits("2362239100018")).toBe("23.622.391/0001-8");
  });

  it("colagem formatada e crua produzem a mesma exibição (AC-02)", () => {
    expect(formatCnpjDigits(CNPJ)).toBe(formatCnpjDigits(CNPJ_MASKED));
    expect(formatCnpjDigits(CNPJ_MASKED)).toBe(CNPJ_MASKED);
  });

  it("letras e símbolos arbitrários são normalizados (AC-03)", () => {
    expect(formatCnpjDigits("23a.622b.391/0001-81!")).toBe(CNPJ_MASKED);
    expect(formatCnpjDigits("CNPJ: 23.622.391/0001-81")).toBe(CNPJ_MASKED);
  });

  it("excedente de dígitos é descartado", () => {
    expect(formatCnpjDigits(`${CNPJ}99`)).toBe(CNPJ_MASKED);
  });
});

describe("formatCpfDigits", () => {
  it("11 dígitos → 000.000.000-00, progressivo", () => {
    expect(formatCpfDigits("52998224725")).toBe("529.982.247-25");
    expect(formatCpfDigits("5299")).toBe("529.9");
    expect(formatCpfDigits("52998224725999")).toBe("529.982.247-25");
  });
});

describe("formatTaxIdForPerson — tipo de pessoa (AC-07)", () => {
  it("pessoa jurídica usa máscara CNPJ", () => {
    expect(formatTaxIdForPerson(CNPJ, "J")).toBe(CNPJ_MASKED);
  });

  it("pessoa física usa máscara CPF", () => {
    expect(formatTaxIdForPerson("52998224725", "F")).toBe("529.982.247-25");
  });

  it("tipo indefinido/outros não ganha máscara ambígua", () => {
    expect(formatTaxIdForPerson(CNPJ, undefined)).toBe(CNPJ);
    expect(formatTaxIdForPerson(CNPJ, "")).toBe(CNPJ);
    expect(formatTaxIdForPerson(CNPJ, "X")).toBe(CNPJ);
  });

  it("CPF excedente em pessoa física mostra dígitos (não esconde payload)", () => {
    expect(formatTaxIdForPerson(CNPJ, "F")).toBe(CNPJ);
  });
});

describe("caret helpers (AC-04)", () => {
  it("digitsBeforePos conta dígitos ignorando separadores", () => {
    expect(digitsBeforePos(CNPJ_MASKED, 0)).toBe(0);
    expect(digitsBeforePos(CNPJ_MASKED, 4)).toBe(3); // "23.6"
    expect(digitsBeforePos(CNPJ_MASKED, 9)).toBe(7); // "23.622.39"→7
    expect(digitsBeforePos(CNPJ_MASKED, CNPJ_MASKED.length)).toBe(14);
  });

  it("caretPosAfterDigits posiciona após o N-ésimo dígito + separador", () => {
    expect(caretPosAfterDigits(CNPJ_MASKED, 0)).toBe(0);
    expect(caretPosAfterDigits(CNPJ_MASKED, 2)).toBe(3); // passa o '.'
    expect(caretPosAfterDigits(CNPJ_MASKED, 3)).toBe(4);
    expect(caretPosAfterDigits(CNPJ_MASKED, 8)).toBe(11); // passa a '/'
    expect(caretPosAfterDigits(CNPJ_MASKED, 14)).toBe(CNPJ_MASKED.length);
    // edição no meio: dígito inserido na 5ª posição mantém caret coerente
    const mid = formatCnpjDigits("23622391000181");
    expect(caretPosAfterDigits(mid, 5)).toBe(7);
  });

  it("apagar separador não desloca a identidade: caret cai após o separador", () => {
    // usuário apaga o '.' em "23.6" (caret em 3): restam 2 dígitos antes —
    // a máscara re-renderiza o '.' e o caret fica logo depois dele.
    const digits = digitsOnly("23.6".slice(0, 3).replace(/\D/g, ""));
    expect(digits).toBe("23");
    expect(caretPosAfterDigits(formatCnpjDigits("236"), 2)).toBe(3);
  });
});
