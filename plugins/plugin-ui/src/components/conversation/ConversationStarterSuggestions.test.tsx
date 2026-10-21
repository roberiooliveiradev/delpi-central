import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ConversationStarterSuggestions,
  STARTER_SUGGESTIONS_DEFAULT_LABEL,
  type ConversationStarterSuggestion,
} from "./ConversationStarterSuggestions";

afterEach(cleanup);

const QA_FIXTURES: ConversationStarterSuggestion[] = [
  {
    id: "data-formats",
    title: "Formatos de dados",
    description: "Ver o que posso consultar",
    draftText: "Quais formatos de dados estão disponíveis?",
    iconKey: "data",
  },
  {
    id: "sipoc-concept",
    title: "O que é SIPOC?",
    description: "Entenda o conceito de processos",
    draftText: "O que é SIPOC?",
    iconKey: "concept",
  },
  {
    id: "available-sources",
    title: "Fontes disponíveis",
    description: "Descobrir o que seu acesso permite",
    draftText: "Quais fontes de informação posso consultar com meu acesso?",
    iconKey: "sources",
  },
  {
    id: "operational-analysis",
    title: "Tipos de análise",
    description: "Explorar o que a DÉLIA pode fazer agora",
    draftText:
      "Que tipos de análise operacional você consegue realizar agora?",
    iconKey: "analysis",
  },
];

function cardButtons() {
  return document.querySelectorAll<HTMLButtonElement>(
    ".delpi-ui-starter-suggestions__card:not(.delpi-ui-starter-suggestions__card--skeleton)",
  );
}

describe("ConversationStarterSuggestions", () => {
  // SS-V01 / SS-F05 — nothing honest to show → nothing rendered.
  it("renders nothing when items is empty (no label, no leftover space)", () => {
    const { container } = render(
      <ConversationStarterSuggestions items={[]} onSelect={vi.fn()} />,
    );
    expect(container.firstElementChild).toBeNull();
  });

  it("renders the labelled section and all four QA fixture cards", () => {
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={vi.fn()}
      />,
    );
    const section = document.querySelector(
      ".delpi-ui-starter-suggestions",
    );
    expect(section).toBeTruthy();
    expect(section?.getAttribute("aria-labelledby")).toBe(
      section?.querySelector(".delpi-ui-starter-suggestions__label")?.id,
    );
    expect(section?.textContent).toContain(
      STARTER_SUGGESTIONS_DEFAULT_LABEL,
    );
    expect(cardButtons()).toHaveLength(4);
    expect(screen.getByText("Formatos de dados")).toBeTruthy();
    expect(screen.getByText("O que é SIPOC?")).toBeTruthy();
    expect(screen.getByText("Fontes disponíveis")).toBeTruthy();
    expect(screen.getByText("Tipos de análise")).toBeTruthy();
  });

  it("renders 1, 2 or 3 items without placeholders", () => {
    for (const count of [1, 2, 3]) {
      cleanup();
      render(
        <ConversationStarterSuggestions
          items={QA_FIXTURES.slice(0, count)}
          onSelect={vi.fn()}
        />,
      );
      expect(cardButtons()).toHaveLength(count);
    }
  });

  it("caps visible cards at maxVisible", () => {
    const six = [
      ...QA_FIXTURES,
      {
        id: "extra-1",
        title: "Extra 1",
        draftText: "Extra um",
      },
      {
        id: "extra-2",
        title: "Extra 2",
        draftText: "Extra dois",
      },
    ];
    render(
      <ConversationStarterSuggestions items={six} onSelect={vi.fn()} />,
    );
    expect(cardButtons()).toHaveLength(4);
    expect(screen.queryByText("Extra 1")).toBeNull();
  });

  // SS-F03 — selection is an intent callback only.
  it("fires onSelect with the item on click; never submits itself", () => {
    const onSelect = vi.fn();
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={onSelect}
      />,
    );
    const card = screen.getByText("O que é SIPOC?").closest("button")!;
    fireEvent.click(card);
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect).toHaveBeenCalledWith(QA_FIXTURES[1]);
  });

  it("uses real buttons — native Enter/Space activation, natural tab order", () => {
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={vi.fn()}
      />,
    );
    for (const card of cardButtons()) {
      expect(card.tagName).toBe("BUTTON");
      expect(card.getAttribute("type")).toBe("button");
    }
  });

  it("without onSelect or when disabled, cards are inert", () => {
    const { unmount } = render(
      <ConversationStarterSuggestions items={QA_FIXTURES} />,
    );
    for (const card of cardButtons()) {
      expect(card.disabled).toBe(true);
    }
    unmount();
    const onSelect = vi.fn();
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={onSelect}
        disabled
      />,
    );
    const card = cardButtons()[0];
    expect(card.disabled).toBe(true);
    fireEvent.click(card);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("honours per-item disabled without hiding the card", () => {
    const onSelect = vi.fn();
    const items = [
      { ...QA_FIXTURES[0], disabled: true },
      QA_FIXTURES[1],
    ];
    render(
      <ConversationStarterSuggestions items={items} onSelect={onSelect} />,
    );
    const cards = cardButtons();
    expect(cards[0].disabled).toBe(true);
    expect(cards[1].disabled).toBe(false);
    fireEvent.click(cards[1]);
    expect(onSelect).toHaveBeenCalledWith(items[1]);
  });

  // SS-V03/SS-V08 — HelpTooltip wrap: the question to insert is described.
  it("links each card to a tooltip describing the draft text", () => {
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={vi.fn()}
      />,
    );
    for (const card of cardButtons()) {
      const desc = card.getAttribute("aria-describedby");
      expect(desc).toBeTruthy();
      expect(document.getElementById(desc!)).toBeNull(); // bubble mounts on demand
    }
    const card = cardButtons()[1];
    fireEvent.mouseEnter(card.parentElement!);
    const descId = card.getAttribute("aria-describedby")!;
    const bubble = document.getElementById(descId);
    expect(bubble).toBeTruthy();
    expect(bubble?.textContent).toContain("O que é SIPOC?");
    expect(bubble?.textContent).toContain("rascunho");
  });

  it("renders the loading state as a bounded decorative skeleton", () => {
    render(
      <ConversationStarterSuggestions
        items={[]}
        loading
        onSelect={vi.fn()}
      />,
    );
    const section = document.querySelector(
      ".delpi-ui-starter-suggestions",
    );
    expect(section).toBeTruthy();
    expect(section?.getAttribute("aria-busy")).toBe("true");
    expect(
      document.querySelectorAll(
        ".delpi-ui-starter-suggestions__card--skeleton",
      ),
    ).toHaveLength(2);
    expect(cardButtons()).toHaveLength(0);
  });

  it("renders an optional status note", () => {
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={vi.fn()}
        note="Edite ou apague o texto atual antes de usar uma sugestão."
      />,
    );
    const note = document.querySelector(
      ".delpi-ui-starter-suggestions__note",
    );
    expect(note?.getAttribute("role")).toBe("status");
    expect(note?.textContent).toContain("Edite ou apague");
  });

  it("applies compact density and className", () => {
    const { container } = render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        density="compact"
        className="extra-class"
        onSelect={vi.fn()}
      />,
    );
    const root = container.firstElementChild!;
    expect(
      root.classList.contains("delpi-ui-starter-suggestions--compact"),
    ).toBe(true);
    expect(root.classList.contains("extra-class")).toBe(true);
  });

  it("keeps the title readable without an icon", () => {
    render(
      <ConversationStarterSuggestions
        items={[{ id: "x", title: "Sem ícone", draftText: "texto" }]}
        onSelect={vi.fn()}
      />,
    );
    expect(screen.getByText("Sem ícone")).toBeTruthy();
    expect(
      document.querySelector(".delpi-ui-starter-suggestions__icon"),
    ).toBeNull();
  });

  // SS-V09 — render-only chrome: no fetch, no storage, no timers.
  it("performs no fetch — render-only, no Core/AuthZ access", () => {
    const spy = vi.spyOn(globalThis, "fetch");
    render(
      <ConversationStarterSuggestions
        items={QA_FIXTURES}
        onSelect={vi.fn()}
      />,
    );
    fireEvent.click(cardButtons()[0]);
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("renders hostile suggestion text as inert text", () => {
    const hostile = '<img src=x onerror=alert(1)><script>alert(2)</script>';
    render(
      <ConversationStarterSuggestions
        items={[{ id: "h", title: hostile, draftText: hostile }]}
        onSelect={vi.fn()}
      />,
    );
    expect(
      document.querySelector(
        ".delpi-ui-starter-suggestions__card-title",
      )?.textContent,
    ).toBe(hostile);
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });
});
