import { describe, expect, it } from "vitest";

import { describeHttpError, describeHttpErrorTitle } from "./apiErrorMessage";

describe("describeHttpError", () => {
  it("explica 429 sem mencionar migrations", () => {
    const message = describeHttpError(429);
    expect(message).toMatch(/muitas requisições/i);
    expect(message).not.toMatch(/migration/i);
    expect(message).not.toMatch(/^Erro HTTP 429/);
  });

  it("prioriza detalhe da API em 4xx (exceto 429)", () => {
    expect(describeHttpError(422, "Início de vigência inválido.")).toBe(
      "Início de vigência inválido.",
    );
  });

  it("usa mensagem amigável para 5xx", () => {
    expect(describeHttpError(503)).toMatch(/indisponível/i);
  });
});

describe("describeHttpErrorTitle", () => {
  it("classifica títulos por status", () => {
    expect(describeHttpErrorTitle(429)).toBe("Muitas requisições");
    expect(describeHttpErrorTitle(403)).toBe("Acesso negado");
    expect(describeHttpErrorTitle(500)).toBe("Serviço indisponível");
  });
});
