/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NewsBoardView } from "./NewsBoardView";
import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("NewsBoardView", () => {
  it("positive: renderiza marca e manchete ativa do board", () => {
    render(<NewsBoardView board={MOCK_PUBLIC_NEWS_BOARD} />);
    expect(screen.getByTestId("delpi-news-board")).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "DELPI News" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[0]!.title }),
    ).toBeInTheDocument();
  });

  it("sibling: botão Próxima avança a manchete", () => {
    render(<NewsBoardView board={MOCK_PUBLIC_NEWS_BOARD} />);
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[1]!.title }),
    ).toBeInTheDocument();
  });

  it("negative: board sem itens mostra estado vazio", () => {
    render(
      <NewsBoardView
        board={{
          ...MOCK_PUBLIC_NEWS_BOARD,
          items: [],
        }}
      />,
    );
    expect(screen.getByText("Nenhuma notícia publicada no momento.")).toBeInTheDocument();
  });
});
