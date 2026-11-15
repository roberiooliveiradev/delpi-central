/** DELPI-MYREQUESTS-ENGINEERING-INTEGRATION-ISOLATION-01 — prova do
 * gate da integração: somente o recorte `raw-material-creation` (ou
 * ausência de filtro de tipo) pode acionar a Engineering API; todos
 * os demais tipos e qualquer recorte de filial são excluídos.
 *
 * A predicação aqui É o ponto único de decisão da chamada — se este
 * teste passa, nenhum fluxo de outro tipo pode disparar a consulta
 * à Engineering API pela listagem unificada.
 */

import { describe, expect, it } from "vitest";

import {
  PRC_LIST_UNAVAILABLE_MESSAGE,
  PRC_REQUEST_TYPE_CODE,
  prcListErrorMessage,
  shouldIncludePrcInList,
} from "./prcIntegrationGate";

describe("shouldIncludePrcInList — gate da integração Engineering API", () => {
  it("tipo canônico raw-material-creation aciona a integração", () => {
    expect(
      shouldIncludePrcInList({ typeCode: "raw-material-creation" }),
    ).toBe(true);
  });

  it("sem filtro de tipo a listagem unificada inclui casos PRC", () => {
    expect(shouldIncludePrcInList({})).toBe(true);
    expect(shouldIncludePrcInList({ typeCode: "" })).toBe(true);
    expect(
      shouldIncludePrcInList({ typeCode: undefined }),
    ).toBe(true);
  });

  it.each([
    "invoice-issuance",
    "process-issue",
    "general-request",
    "ticket-opening",
    "qualquer-outro-tipo",
  ])("tipo %s NUNCA aciona a Engineering API", (typeCode) => {
    expect(shouldIncludePrcInList({ typeCode })).toBe(false);
  });

  it("recorte por filial exclui PRC (contrato sem filial)", () => {
    expect(
      shouldIncludePrcInList({ typeCode: "", branch: "01" }),
    ).toBe(false);
    expect(
      shouldIncludePrcInList({
        typeCode: "raw-material-creation",
        branch: "02",
      }),
    ).toBe(false);
  });

  it("identificador canônico é o código estável, não nome traduzido", () => {
    expect(PRC_REQUEST_TYPE_CODE).toBe("raw-material-creation");
    expect(
      shouldIncludePrcInList({ typeCode: "Criação de matéria-prima" }),
    ).toBe(false);
  });
});

describe("prcListErrorMessage — erro contextual sem internals", () => {
  it("retorna mensagem estática, nunca o detalhe do backend", () => {
    const msg = prcListErrorMessage();
    expect(msg).toBe(PRC_LIST_UNAVAILABLE_MESSAGE);
    expect(msg).not.toContain("postgres");
    expect(msg).not.toContain("fe_sendauth");
    expect(msg).not.toMatch(/172\.|5432|ECONN|ETIMEDOUT/);
  });
});
