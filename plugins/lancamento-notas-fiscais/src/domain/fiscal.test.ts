import { describe, expect, it } from "vitest";
import {
  normalizeDocumentInput,
  normalizeSeriesInput,
  parseAmountInput,
  sanitizeAmountTyping,
  sanitizeDocumentTyping,
} from "./fiscal";

describe("normalizeDocumentInput", () => {
  it("completa até 9 dígitos na apresentação e na chave", () => {
    const result = normalizeDocumentInput("123456");
    expect(result.valid).toBe(true);
    expect(result.display).toBe("000123456");
    expect(result.matchKey).toBe("000123456");
  });

  it("preserva 9 dígitos", () => {
    const result = normalizeDocumentInput("123456789");
    expect(result.display).toBe("123456789");
    expect(result.matchKey).toBe("123456789");
  });

  it("rejeita mais de 9 dígitos sem truncar silenciosamente o valor válido", () => {
    const result = normalizeDocumentInput("1234567890");
    expect(result.valid).toBe(false);
    expect(sanitizeDocumentTyping("1234567890")).toBe("123456789");
  });
});

describe("parseAmountInput", () => {
  it("aceita vírgula e ponto", () => {
    expect(parseAmountInput("1.100,50")).toBe(1100.5);
    expect(parseAmountInput("1100,5")).toBe(1100.5);
    expect(parseAmountInput("1100.50")).toBe(1100.5);
    expect(sanitizeAmountTyping("1100,5a")).toBe("1100,5");
  });
});

describe("normalizeSeriesInput", () => {
  it("aplica trim e uppercase com limite 3", () => {
    expect(normalizeSeriesInput(" a1 ")).toBe("A1");
    expect(normalizeSeriesInput("abcd")).toBe("ABC");
  });
});
