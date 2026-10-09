import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { parseGeneralRequestPayload } from "../domain/generalRequestPayload";

describe("parseGeneralRequestPayload", () => {
  it("normaliza título e descrição", () => {
    const view = parseGeneralRequestPayload({
      title: "  Revisar fluxo de aprovação  ",
      description: "Detalhes\nda demanda.",
    });
    expect(view).toEqual({
      title: "Revisar fluxo de aprovação",
      description: "Detalhes\nda demanda.",
    });
  });

  it("tolera payload vazio, parcial ou inválido", () => {
    expect(parseGeneralRequestPayload(null)).toEqual({
      title: null,
      description: null,
    });
    expect(parseGeneralRequestPayload({})).toEqual({
      title: null,
      description: null,
    });
    expect(parseGeneralRequestPayload({ title: 42 })).toEqual({
      title: "42",
      description: null,
    });
  });
});

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("GeneralRequestPayloadPanel structural", () => {
  it("título em destaque e descrição em bloco — não grade lado a lado", () => {
    const src = read("features/general-request/ui/GeneralRequestPayloadPanel.tsx");
    expect(src).toContain("my-requests-general-request__title");
    expect(src).toContain("my-requests-general-request__description");
    expect(src).toContain("<h3");
    expect(src).toContain("<p");
    // sem DetailFields: título e descrição nunca ficam lado a lado num grid
    expect(src).not.toContain("DetailFields");
  });

  it("usa o parser dedicado — não acessa o payload bruto", () => {
    const src = read("features/general-request/ui/GeneralRequestPayloadPanel.tsx");
    expect(src).toContain("parseGeneralRequestPayload");
    expect(src).not.toMatch(/payload\.(title|description)/);
  });
});

describe("RequestDetailPage — montagem do chamado", () => {
  it("renderiza o painel do chamado antes dos metadados da solicitação", () => {
    const src = read("pages/RequestDetailPage.tsx");
    expect(src).toContain('request.type_code === "general-request"');
    expect(src).toContain("GeneralRequestPayloadPanel");
    const idxPanel = src.indexOf('request.type_code === "general-request"');
    const idxMeta = src.indexOf('title="Dados da solicitação"');
    expect(idxPanel).toBeGreaterThan(-1);
    expect(idxMeta).toBeGreaterThan(idxPanel);
  });

  it("o card genérico de formulário exclui general-request", () => {
    const src = read("domain/schemaPayload.ts");
    expect(src).toContain('"general-request"');
  });
});
