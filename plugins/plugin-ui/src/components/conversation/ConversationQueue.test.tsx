import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ConversationQueue,
  type ConversationQueueItem,
} from "./ConversationQueue";

afterEach(() => {
  cleanup();
});

const ITEMS: ConversationQueueItem[] = [
  {
    id: "a",
    label: "Comparar indicadores de SC e ES",
    ordinal: 1,
    status: "queued",
    canMoveDown: true,
    canRemove: true,
  },
  {
    id: "b",
    label: "Consultar chamados de TI abertos esta semana",
    ordinal: 2,
    status: "queued",
    canMoveUp: true,
    canMoveDown: true,
    canRemove: true,
  },
  {
    id: "c",
    label: "Resumir principais desvios do mês anterior",
    ordinal: 3,
    status: "blocked",
    reason: "aguardando dependência",
    canMoveUp: true,
    canRemove: false,
  },
];

describe("ConversationQueue (doc 71 — F03-A)", () => {
  it("CQ-V01: renders nothing with zero items and no states", () => {
    const { container } = render(<ConversationQueue items={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("CQ-V02: collapsed by default with honest count and next preview", () => {
    render(<ConversationQueue items={ITEMS} />);
    const header = screen.getByRole("button", {
      name: /3 solicitações aguardando/,
    });
    expect(header.getAttribute("aria-expanded")).toBe("false");
    expect(header.textContent).toContain("Próxima:");
    // item titles are not visible while collapsed
    expect(screen.queryByText(ITEMS[1]!.label)).toBeNull();
  });

  it("singular count label for one item", () => {
    render(<ConversationQueue items={[ITEMS[0]!]} />);
    expect(
      screen.getByRole("button", { name: /1 solicitação aguardando/ }),
    ).toBeTruthy();
  });

  it("CQ-V03: expand/collapse via header button with aria-controls", () => {
    const onExpandedChange = vi.fn();
    render(
      <ConversationQueue items={ITEMS} onExpandedChange={onExpandedChange} />,
    );
    const header = screen.getByRole("button", {
      name: /3 solicitações aguardando/,
    });
    fireEvent.click(header);
    expect(onExpandedChange).toHaveBeenCalledWith(true);
    expect(header.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText(ITEMS[1]!.label)).toBeTruthy();
    expect(
      document.getElementById(header.getAttribute("aria-controls")!),
    ).toBeTruthy();
    fireEvent.click(header);
    expect(onExpandedChange).toHaveBeenCalledWith(false);
  });

  it("controlled expanded prop wins", () => {
    render(<ConversationQueue items={ITEMS} expanded={true} />);
    expect(screen.getByText(ITEMS[2]!.label)).toBeTruthy();
  });

  it("full label available via title on truncation", () => {
    render(<ConversationQueue items={ITEMS} expanded={true} />);
    const label = screen.getByText(ITEMS[0]!.label);
    expect(label.getAttribute("title")).toBe(ITEMS[0]!.label);
  });

  it("CQ-V04: reorder/remove controls fire intent callbacks per item", () => {
    const onMoveUp = vi.fn();
    const onMoveDown = vi.fn();
    const onRemove = vi.fn();
    render(
      <ConversationQueue
        items={ITEMS}
        expanded={true}
        onMoveUp={onMoveUp}
        onMoveDown={onMoveDown}
        onRemove={onRemove}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: `Mover "${ITEMS[1]!.label}" para cima`,
      }),
    );
    expect(onMoveUp).toHaveBeenCalledWith("b");
    fireEvent.click(
      screen.getByRole("button", {
        name: `Mover "${ITEMS[0]!.label}" para baixo`,
      }),
    );
    expect(onMoveDown).toHaveBeenCalledWith("a");
    fireEvent.click(
      screen.getByRole("button", {
        name: `Remover "${ITEMS[1]!.label}" da fila`,
      }),
    );
    expect(onRemove).toHaveBeenCalledWith("b");
  });

  it("ineligible actions render disabled — never fake a grant", () => {
    render(
      <ConversationQueue
        items={ITEMS}
        expanded={true}
        onMoveUp={() => {}}
        onMoveDown={() => {}}
        onRemove={() => {}}
      />,
    );
    // first item cannot move up; blocked item cannot move down or be removed
    const upFirst = screen.getByRole("button", {
      name: `Mover "${ITEMS[0]!.label}" para cima`,
    });
    expect((upFirst as HTMLButtonElement).disabled).toBe(true);
    const removeBlocked = screen.getByRole("button", {
      name: `Remover "${ITEMS[2]!.label}" da fila`,
    });
    expect((removeBlocked as HTMLButtonElement).disabled).toBe(true);
    // missing callbacks also disable
    cleanup();
    render(<ConversationQueue items={ITEMS} expanded={true} />);
    const any = screen.getAllByRole("button", { name: /Mover "/ });
    expect(any.every((b) => (b as HTMLButtonElement).disabled)).toBe(true);
  });

  it("blocked status is identified without relying on colour alone", () => {
    render(<ConversationQueue items={ITEMS} expanded={true} />);
    expect(
      screen.getByText(/Bloqueado — aguardando dependência/),
    ).toBeTruthy();
  });

  it("CQ-V05: loading / unavailable / error honest states", () => {
    const { rerender } = render(
      <ConversationQueue items={[]} loading={true} />,
    );
    expect(screen.getByText("Carregando fila…")).toBeTruthy();
    rerender(<ConversationQueue items={[]} unavailable={true} />);
    expect(
      screen.getByText("Fila temporariamente indisponível."),
    ).toBeTruthy();
    rerender(<ConversationQueue items={[]} error="Falha ao ler a fila." />);
    expect(screen.getByRole("alert").textContent).toContain(
      "Falha ao ler a fila.",
    );
  });

  it("no surface means the header does not reserve space", () => {
    const { container } = render(
      <ConversationQueue items={[]} expanded={false} />,
    );
    expect(container.innerHTML).toBe("");
  });
});
