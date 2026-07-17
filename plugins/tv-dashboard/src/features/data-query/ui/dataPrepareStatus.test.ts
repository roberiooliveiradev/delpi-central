import { describe, expect, it } from "vitest";

import {
  resolveDataPrepareStatus,
  type DataPrepareStatusInput,
} from "./dataPrepareStatus";

function input(
  overrides: Partial<DataPrepareStatusInput> = {},
): DataPrepareStatusInput {
  return {
    compileStatus: "success",
    compileError: null,
    previewStatus: "success",
    previewError: null,
    previewUpdatedAt: 1_000_000,
    hasPreview: true,
    rowCount: 12,
    runtimeErrorCount: 0,
    dirtyCount: 0,
    isApplying: false,
    applyError: null,
    now: 1_030_000,
    ...overrides,
  };
}

describe("resolveDataPrepareStatus", () => {
  it("prioriza falhas do fluxo", () => {
    expect(resolveDataPrepareStatus(input({ applyError: "Falha ao aplicar" }))).toEqual({
      tone: "error",
      message: "Falha ao aplicar",
      meta: null,
    });
  });

  it("distingue carga inicial de atualização sem apagar dados", () => {
    expect(
      resolveDataPrepareStatus(
        input({ previewStatus: "loading", hasPreview: false }),
      ).message,
    ).toBe("Carregando prévia…");
    expect(
      resolveDataPrepareStatus(
        input({ previewStatus: "loading", hasPreview: true }),
      ).message,
    ).toBe("Atualizando prévia…");
  });

  it("informa erros localizados sem transformar a prévia inteira em falha", () => {
    expect(resolveDataPrepareStatus(input({ runtimeErrorCount: 3 }))).toMatchObject({
      tone: "warning",
      message: "3 erro(s) de célula na prévia",
    });
  });

  it("resume atualização, linhas e alterações pendentes", () => {
    expect(resolveDataPrepareStatus(input({ dirtyCount: 2 }))).toEqual({
      tone: "success",
      message: "Prévia atualizada",
      meta: "atualizado há 30s · 12 linha(s) · 2 consulta(s) alterada(s)",
    });
  });
});
