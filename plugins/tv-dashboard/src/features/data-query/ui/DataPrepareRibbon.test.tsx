import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DataQueryPreview } from "../domain/dataQueryTypes";
import { DataPrepareRibbon } from "./DataPrepareRibbon";

afterEach(cleanup);

const preview: DataQueryPreview = {
  columns: [
    { key: "codigo", label: "Código", type: "text", nullable: false, typeSource: "declared" },
    { key: "valor", label: "Valor", type: "number", nullable: false, typeSource: "declared" },
  ],
  rows: [{ codigo: "A-1", valor: 12 }],
  returnedRows: 1,
  availableRows: 1,
  truncated: false,
  isSample: false,
  selectedStepName: "Fonte",
  diagnostics: [],
};

describe("DataPrepareRibbon M Fase 5", () => {
  it("gera somente comandos tipados para mutação canônica", () => {
    const mutate = vi.fn();
    render(
      <DataPrepareRibbon
        selectedColumnKey="codigo"
        selectedStepName="Fonte"
        preview={preview}
        loading={false}
        availableQueries={["Histórico"]}
        onRefresh={() => undefined}
        onMutate={mutate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Remover coluna" }));
    expect(mutate).toHaveBeenLastCalledWith({
      type: "insert_step",
      afterStepName: "Fonte",
      stepName: "Colunas removidas",
      operation: "remove_columns",
      arguments: { columns: ["codigo"] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Acrescentar consulta" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "append_queries",
      arguments: { queries: ["Histórico"] },
    });

    fireEvent.click(screen.getByRole("button", { name: "Mesclar consulta" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "nested_join",
      arguments: {
        query: "Histórico",
        leftKeys: ["codigo"],
        rightKeys: ["codigo"],
      },
    });
  });

  it("expõe ações de coluna acessíveis sem concatenar M", () => {
    const mutate = vi.fn();
    render(
      <DataPrepareRibbon
        selectedColumnKey="codigo"
        selectedStepName="Etapa estável"
        preview={preview}
        loading={false}
        onRefresh={() => undefined}
        onMutate={mutate}
      />,
    );
    fireEvent.click(screen.getByRole("tab", { name: "Adicionar coluna" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Nome da nova coluna" }), {
      target: { value: "Código cópia" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Duplicar coluna" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      afterStepName: "Etapa estável",
      operation: "duplicate_column",
      arguments: { column: "codigo", newName: "Código cópia" },
    });
  });

  it("cobre linhas, tipos, erros e operações de forma por comandos tipados", () => {
    const mutate = vi.fn();
    render(
      <DataPrepareRibbon
        selectedColumnKey="codigo"
        selectedStepName="Fonte"
        preview={preview}
        loading={false}
        onRefresh={() => undefined}
        onMutate={mutate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Manter intervalo" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "range_rows",
      arguments: { offset: 0, count: 10 },
    });

    fireEvent.click(screen.getByRole("tab", { name: "Transformar" }));
    fireEvent.click(screen.getByRole("button", { name: "Tipo de destino" }));
    fireEvent.click(screen.getByRole("button", { name: /^Data$/ }));
    fireEvent.click(screen.getByRole("button", { name: "Alterar tipo" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "changeType",
      arguments: { column: "codigo", to: "date" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Agrupar linhas" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "group_rows",
      arguments: { keys: ["codigo"], valueColumn: "valor", aggregate: "sum" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Anular dinamização" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "unpivot",
      arguments: { columns: ["codigo"] },
    });
  });

  it("mantém coluna personalizada como expressão explícita enviada ao backend", () => {
    const mutate = vi.fn();
    render(
      <DataPrepareRibbon
        selectedColumnKey="codigo"
        selectedStepName="Fonte"
        preview={preview}
        loading={false}
        onRefresh={() => undefined}
        onMutate={mutate}
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Adicionar coluna" }));
    fireEvent.change(screen.getByRole("textbox", { name: "Nome da nova coluna" }), {
      target: { value: "Código normalizado" },
    });
    fireEvent.change(
      screen.getByRole("textbox", { name: "Expressão da coluna personalizada" }),
      { target: { value: "Text.Upper([codigo])" } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Coluna personalizada" }));
    expect(mutate.mock.calls.at(-1)?.[0]).toMatchObject({
      operation: "add_custom_column",
      arguments: {
        newName: "Código normalizado",
        expression: "Text.Upper([codigo])",
      },
    });
  });
});
