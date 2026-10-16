import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConversationReception } from "./ConversationReception";

afterEach(cleanup);

describe("ConversationReception", () => {
  it("renders title, description and note", () => {
    render(
      <ConversationReception
        title="Como posso ajudar você hoje?"
        description="Converse com a inteligência operacional."
        note="A conversa não é salva."
      />,
    );
    expect(document.querySelector("h2")?.textContent).toBe(
      "Como posso ajudar você hoje?",
    );
    expect(document.body.textContent).toContain(
      "Converse com a inteligência operacional.",
    );
    expect(document.body.textContent).toContain("A conversa não é salva.");
  });

  it("renders the greeting subordinate to the title when supplied", () => {
    render(
      <ConversationReception
        greeting="Bom dia, Robério."
        title="Como posso ajudar você hoje?"
      />,
    );
    const greeting = document.querySelector(
      ".delpi-ui-conversation-reception__greeting",
    );
    const title = document.querySelector(
      ".delpi-ui-conversation-reception__title",
    );
    expect(greeting?.textContent).toBe("Bom dia, Robério.");
    // greeting precedes the title in reading order
    expect(
      greeting!.compareDocumentPosition(title!) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("omits the greeting element when absent", () => {
    render(<ConversationReception title="Como posso ajudar você hoje?" />);
    expect(
      document.querySelector(".delpi-ui-conversation-reception__greeting"),
    ).toBeNull();
  });

  it("renders the avatar slot as decorative", () => {
    render(
      <ConversationReception
        avatar={<span data-testid="mark">avatar</span>}
        title="t"
      />,
    );
    const slot = document.querySelector(
      ".delpi-ui-conversation-reception__avatar",
    );
    expect(slot?.getAttribute("aria-hidden")).toBe("true");
  });

  it("labels the section by the title — no status/alert/live region", () => {
    const { container } = render(
      <ConversationReception title="Como posso ajudar você hoje?" />,
    );
    const section = container.querySelector("section");
    expect(section?.getAttribute("aria-labelledby")).toBe(
      section?.querySelector("h2")?.id,
    );
    expect(section?.getAttribute("role")).toBeNull();
    expect(container.querySelector("[aria-live]")).toBeNull();
    expect(container.querySelector("[role=status]")).toBeNull();
    expect(container.querySelector("[role=alert]")).toBeNull();
  });

  it("applies compact density and className", () => {
    const { container } = render(
      <ConversationReception
        title="t"
        density="compact"
        className="custom-reception"
      />,
    );
    const root = container.firstElementChild!;
    expect(root.classList.contains("delpi-ui-conversation-reception")).toBe(
      true,
    );
    expect(
      root.classList.contains("delpi-ui-conversation-reception--compact"),
    ).toBe(true);
    expect(root.classList.contains("custom-reception")).toBe(true);
  });

  it("renders hostile display text as inert text", () => {
    const hostile = '<img src=x onerror=alert(1)><script>alert(2)</script>';
    render(<ConversationReception greeting={hostile} title="t" />);
    expect(
      document.querySelector(".delpi-ui-conversation-reception__greeting")
        ?.textContent,
    ).toBe(hostile);
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });

  it("wraps long names/descriptions without fixed-width assumptions", () => {
    const long = `Bom dia, ${"A".repeat(120)}.`;
    const { container } = render(
      <ConversationReception greeting={long} title="t" />,
    );
    expect(
      container.querySelector(".delpi-ui-conversation-reception__greeting")
        ?.textContent,
    ).toBe(long);
  });

  it("performs no fetch — chrome is render-only, no Core access", () => {
    const spy = vi.spyOn(globalThis, "fetch");
    render(<ConversationReception title="t" />);
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
});
