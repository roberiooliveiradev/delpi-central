import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { DataQueryDraft } from "../domain/dataQueryTypes";
import { DataPrepareColumnMenu, type ColumnMenuTarget } from "./DataPrepareColumnMenu";
import { DataPrepareQueryList } from "./DataPrepareQueryList";

afterEach(cleanup);

const target: ColumnMenuTarget = {
  position: { x: 40, y: 40 },
  columnKey: "codigo",
  columnLabel: "Código",
  columnType: "text",
  cellValue: "A-1",
};

describe("DataPrepareColumnMenu", () => {
  it("fecha ao clicar fora do popover", () => {
    const onClose = vi.fn();
    render(<DataPrepareColumnMenu target={target} onClose={onClose} onInsert={() => undefined} />);

    expect(screen.getByRole("menuitem", { name: "Renomear coluna" })).toBeTruthy();
    fireEvent.pointerDown(document.body);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("mostra o input de renomear somente após acionar a ação", () => {
    const onInsert = vi.fn();
    render(
      <DataPrepareColumnMenu target={target} onClose={() => undefined} onInsert={onInsert} />,
    );

    expect(screen.queryByLabelText("Novo nome da coluna")).toBeNull();
    fireEvent.click(screen.getByRole("menuitem", { name: "Renomear coluna" }));

    const input = screen.getByLabelText("Novo nome da coluna");
    fireEvent.change(input, { target: { value: "Chave" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));

    expect(onInsert).toHaveBeenCalledWith("Colunas renomeadas", "rename", {
      from: "codigo",
      to: "Chave",
    });
  });

  it("filtra pelo valor da célula selecionada", () => {
    const onInsert = vi.fn();
    render(
      <DataPrepareColumnMenu target={target} onClose={() => undefined} onInsert={onInsert} />,
    );

    fireEvent.click(screen.getByRole("menuitem", { name: 'Manter linhas iguais a "A-1"' }));
    expect(onInsert).toHaveBeenCalledWith("Linhas filtradas", "filter", {
      column: "codigo",
      cmp: "eq",
      value: "A-1",
    });
  });
});

const drafts = [
  { sourceId: "q1", queryName: "OEE", dirty: false },
  { sourceId: "q2", queryName: "Turnos", dirty: true },
] as unknown as DataQueryDraft[];

describe("DataPrepareQueryList", () => {
  it("renomeia a consulta pelo menu de botão direito com input inline", async () => {
    const onRename = vi.fn().mockResolvedValue(undefined);
    const onSelect = vi.fn();
    render(
      <DataPrepareQueryList
        drafts={drafts}
        activeQueryId="q1"
        onSelect={onSelect}
        onRename={onRename}
      />,
    );

    expect(screen.queryByLabelText(/^Novo nome de/)).toBeNull();
    fireEvent.contextMenu(screen.getByRole("tab", { name: /OEE/ }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Renomear" }));

    const input = screen.getByLabelText("Novo nome de OEE");
    fireEvent.change(input, { target: { value: "OEE global" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(onRename).toHaveBeenCalledWith("OEE global");
  });
});
