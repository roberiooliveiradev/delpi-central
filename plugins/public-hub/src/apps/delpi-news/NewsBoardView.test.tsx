/** @vitest-environment jsdom */

import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DELPI_NEWS_DEMO_BANNER } from "./demoMode";
import { NewsBoardView } from "./NewsBoardView";
import { MOCK_PUBLIC_NEWS_BOARD } from "./mockFeed";
import type { PublicNewsBoard } from "./types";

function boardWith(overrides: Partial<PublicNewsBoard>): PublicNewsBoard {
  return { ...MOCK_PUBLIC_NEWS_BOARD, ...overrides };
}

function installAnimationFramePolyfill() {
  window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
    return window.setTimeout(() => cb(performance.now()), 16) as unknown as number;
  }) as typeof window.requestAnimationFrame;
  window.cancelAnimationFrame = ((id: number) => {
    window.clearTimeout(id);
  }) as typeof window.cancelAnimationFrame;
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
  installAnimationFramePolyfill();
});

describe("NewsBoardView", () => {
  beforeEach(() => {
    installAnimationFramePolyfill();
  });

  it("positive: renderiza marca, manchete e identificação de demonstração", () => {
    render(<NewsBoardView board={MOCK_PUBLIC_NEWS_BOARD} />);
    expect(screen.getByTestId("delpi-news-board")).toHaveAttribute("data-demo", "true");
    expect(screen.getByTestId("delpi-news-demo-banner")).toHaveTextContent(DELPI_NEWS_DEMO_BANNER);
    expect(screen.getByRole("heading", { level: 1, name: /Demonstração/i })).toBeInTheDocument();
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

  it("volta ao início após a última notícia", () => {
    render(<NewsBoardView board={MOCK_PUBLIC_NEWS_BOARD} />);
    const last = MOCK_PUBLIC_NEWS_BOARD.items.length - 1;
    for (let i = 0; i < last; i += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    }
    expect(
      screen.getByRole("heading", {
        level: 2,
        name: MOCK_PUBLIC_NEWS_BOARD.items[last]!.title,
      }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[0]!.title }),
    ).toBeInTheDocument();
  });

  it("navegação por teclado avança e retrocede", () => {
    render(<NewsBoardView board={MOCK_PUBLIC_NEWS_BOARD} />);
    fireEvent.keyDown(window, { key: "ArrowRight" });
    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[1]!.title }),
    ).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[0]!.title }),
    ).toBeInTheDocument();
  });

  it("avanço automático pelo temporizador respeita a duração", async () => {
    let now = 0;
    const queue: FrameRequestCallback[] = [];
    window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
      queue.push(cb);
      return queue.length;
    }) as typeof window.requestAnimationFrame;
    window.cancelAnimationFrame = (() => undefined) as typeof window.cancelAnimationFrame;
    vi.spyOn(performance, "now").mockImplementation(() => now);

    render(
      <NewsBoardView
        board={boardWith({
          rotation_interval_sec: 1,
          items: MOCK_PUBLIC_NEWS_BOARD.items.slice(0, 2),
        })}
      />,
    );

    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[0]!.title }),
    ).toBeInTheDocument();
    expect(queue.length).toBeGreaterThan(0);

    await act(async () => {
      now = 1000;
      const pending = queue.splice(0, queue.length);
      for (const cb of pending) {
        cb(now);
      }
    });

    expect(
      screen.getByRole("heading", { level: 2, name: MOCK_PUBLIC_NEWS_BOARD.items[1]!.title }),
    ).toBeInTheDocument();
  });

  it("negative: board sem itens mostra estado vazio", () => {
    render(<NewsBoardView board={boardWith({ items: [] })} />);
    expect(screen.getByTestId("delpi-news-board-empty")).toBeInTheDocument();
    expect(screen.getByText("Nenhuma notícia disponível para exibição.")).toBeInTheDocument();
    expect(screen.getByTestId("delpi-news-demo-banner")).toBeInTheDocument();
  });

  it("ausência de imagem mostra placeholder", () => {
    render(
      <NewsBoardView
        board={boardWith({
          items: [
            {
              ...MOCK_PUBLIC_NEWS_BOARD.items[1]!,
              image_url: null,
            },
          ],
        })}
      />,
    );
    expect(screen.getByText("Sem imagem")).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("manchete longa permanece no documento com clamp visual", () => {
    const longTitle = MOCK_PUBLIC_NEWS_BOARD.items[2]!.title;
    render(
      <NewsBoardView
        board={boardWith({
          items: [MOCK_PUBLIC_NEWS_BOARD.items[2]!],
        })}
      />,
    );
    const heading = screen.getByRole("heading", { level: 2, name: longTitle });
    expect(heading).toBeInTheDocument();
    expect(heading.className).toContain("dn-pub__headline");
  });
});
