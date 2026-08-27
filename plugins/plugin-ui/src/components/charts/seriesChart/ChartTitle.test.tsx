import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { ChartTitle } from "./ChartTitle";

beforeAll(() => {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
});

afterEach(() => {
  cleanup();
});

describe("ChartTitle edit remount", () => {
  it("ao sair da edição não deixa título duplicado no host (texto órfão + DeckContentRunsView)", () => {
    const onPartContentCommit = vi.fn();
    const interaction = {
      editingPart: { kind: "title" as const },
      selectedPart: { kind: "title" as const },
      onPartContentCommit,
      onPartPointerDown: vi.fn(),
      onPartDoubleClick: vi.fn(),
    };

    const { rerender, container } = render(
      <ChartTitle title="OTD WEG AMAZONIA" interaction={interaction} />,
    );

    const editor = screen.getByRole("textbox", { name: "Editar título do gráfico" });
    expect(editor.textContent).toContain("OTD WEG AMAZONIA");

    fireEvent.blur(editor);

    rerender(
      <ChartTitle
        title="OTD WEG AMAZONIA"
        interaction={{
          ...interaction,
          editingPart: null,
        }}
      />,
    );

    const host = container.querySelector(".delpi-ui-series-chart__title");
    expect(host).toBeTruthy();
    const textNodes: string[] = [];
    const walk = (node: Node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const value = (node.textContent ?? "").replace(/\u00a0/g, " ").trim();
        if (value) textNodes.push(value);
        return;
      }
      node.childNodes.forEach(walk);
    };
    walk(host!);
    const titleHits = textNodes.filter((value) => value.includes("OTD WEG AMAZONIA"));
    expect(titleHits).toHaveLength(1);
    expect(host!.textContent?.replace(/\u00a0/g, " ").trim()).toBe("OTD WEG AMAZONIA");
  });
});
