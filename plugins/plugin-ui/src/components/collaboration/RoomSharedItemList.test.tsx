import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RoomSharedItemList, roomSharedItemListBemClasses } from "./RoomSharedItemList";

const classNames = roomSharedItemListBemClasses("delpi-ui");

afterEach(() => {
  cleanup();
});

describe("RoomSharedItemList", () => {
  it("mostra a linha e abre pelo id, sem consultar API", () => {
    const onOpen = vi.fn();
    render(
      <RoomSharedItemList
        classNames={classNames}
        listAriaLabel="Itens compartilhados"
        onOpen={onOpen}
        toolbar={<span>Arquivos</span>}
        items={[
          {
            id: "file-1",
            title: "proposta.pdf",
            subtitle: "PDF",
            whenLabel: "hoje",
            whoLabel: "Ana",
            ariaLabel: "Abrir proposta.pdf",
          },
        ]}
        icon={() => <span data-testid="icon" />}
      />,
    );
    expect(screen.getByText("Arquivos")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Abrir proposta.pdf" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Abrir proposta.pdf" }));
    expect(onOpen).toHaveBeenCalledWith("file-1");
  });

  it("mostra o estado vazio quando não há itens", () => {
    render(
      <RoomSharedItemList
        classNames={classNames}
        listAriaLabel="Itens compartilhados"
        onOpen={() => undefined}
        items={[]}
      >
        <p>Nenhum arquivo</p>
      </RoomSharedItemList>,
    );
    expect(screen.getByText("Nenhum arquivo")).toBeTruthy();
    expect(screen.queryByRole("list")).toBeNull();
  });
});
