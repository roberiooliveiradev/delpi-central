import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import App from "../App";
import {
  demoMoveItem,
  demoRemoveItem,
  resolveQueueDemo,
} from "./queueDemo";

const DEMO_ENV = { DEV: true } as const;
const PROD_ENV = { DEV: false } as const;

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
});

describe("queueDemo resolver (doc 71 — F03-A QA fixture)", () => {
  it("never activates outside the demo gate, even with the param", () => {
    expect(
      resolveQueueDemo("?delia-demo-queue=pending", PROD_ENV),
    ).toBeNull();
  });

  it("stays null without the query param", () => {
    expect(resolveQueueDemo("", DEMO_ENV)).toBeNull();
    expect(resolveQueueDemo("?other=1", DEMO_ENV)).toBeNull();
  });

  it("resolves pending fixture behind the gate", () => {
    const state = resolveQueueDemo("?delia-demo-queue=pending", DEMO_ENV);
    expect(state?.items.length).toBe(3);
    expect(state?.items[0]?.status).toBe("queued");
  });

  it("resolves honest state variants", () => {
    expect(
      resolveQueueDemo("?delia-demo-queue=loading", DEMO_ENV)?.loading,
    ).toBe(true);
    expect(
      resolveQueueDemo("?delia-demo-queue=error", DEMO_ENV)?.error,
    ).toBeTruthy();
    expect(
      resolveQueueDemo("?delia-demo-queue=unavailable", DEMO_ENV)
        ?.unavailable,
    ).toBe(true);
    expect(
      resolveQueueDemo("?delia-demo-queue=blocked", DEMO_ENV)?.items.some(
        (i) => i.status === "blocked",
      ),
    ).toBe(true);
    expect(
      resolveQueueDemo("?delia-demo-queue=one", DEMO_ENV)?.items.length,
    ).toBe(1);
  });

  it("unknown variant falls back to pending — never silent empty", () => {
    const state = resolveQueueDemo("?delia-demo-queue=zzz", DEMO_ENV);
    expect(state?.items.length).toBe(3);
  });

  it("fixture intents reorder/remove locally with renumbered ordinals", () => {
    const state = resolveQueueDemo("?delia-demo-queue=pending", DEMO_ENV)!;
    const moved = demoMoveItem(state.items, "demo-q2", "up");
    expect(moved.map((i) => i.id)).toEqual([
      "demo-q2",
      "demo-q1",
      "demo-q3",
    ]);
    expect(moved.map((i) => i.ordinal)).toEqual([1, 2, 3]);
    const removed = demoRemoveItem(state.items, "demo-q1");
    expect(removed.map((i) => i.id)).toEqual(["demo-q2", "demo-q3"]);
    expect(removed.map((i) => i.ordinal)).toEqual([1, 2]);
  });
});

describe("ConversationQueue — App integration (doc 71 §13)", () => {
  it("CQ-V01: production path renders no queue surface above the composer", () => {
    render(<App />);
    expect(
      document.querySelector(".delpi-ui-conversation-queue"),
    ).toBeNull();
    // Composer still rendered and usable.
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toBeTruthy();
  });

  it("QA fixture shows collapsed header, expands, and moves items locally", () => {
    window.history.replaceState({}, "", "/?delia-demo-queue=pending");
    render(<App />);
    const header = screen.getByRole("button", {
      name: /3 solicitações aguardando/,
    });
    expect(header.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(header);
    expect(header.getAttribute("aria-expanded")).toBe("true");

    // Reorder intent moves item up in the fixture state.
    fireEvent.click(
      screen.getByRole("button", {
        name: /Mover "Consultar chamados de TI abertos esta semana" para cima/,
      }),
    );
    const labels = Array.from(
      document.querySelectorAll(".delpi-ui-conversation-queue__label"),
    ).map((el) => el.textContent);
    expect(labels[0]).toContain("Consultar chamados de TI abertos");
    // Ordinals follow the new order.
    const ordinals = Array.from(
      document.querySelectorAll(".delpi-ui-conversation-queue__ordinal"),
    ).map((el) => el.textContent);
    expect(ordinals).toEqual(["1.", "2.", "3."]);
  });

  it("fixture remove drops the item and renumbers", () => {
    window.history.replaceState({}, "", "/?delia-demo-queue=pending");
    render(<App />);
    fireEvent.click(
      screen.getByRole("button", { name: /3 solicitações aguardando/ }),
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: /Remover "Comparar indicadores de SC e ES no período" da fila/,
      }),
    );
    expect(
      screen.getByRole("button", { name: /2 solicitações aguardando/ }),
    ).toBeTruthy();
  });

  it("loading/error variants render honest states, not fake items", () => {
    window.history.replaceState({}, "", "/?delia-demo-queue=loading");
    render(<App />);
    expect(screen.getByText("Carregando fila…")).toBeTruthy();
    cleanup();
    window.history.replaceState({}, "", "/?delia-demo-queue=error");
    render(<App />);
    expect(
      screen.getByText("Não foi possível ler a fila agora."),
    ).toBeTruthy();
  });
});
