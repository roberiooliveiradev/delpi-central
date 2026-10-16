import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeliaReception } from "./DeliaReception";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

const GREETING_SEL = ".delpi-ui-conversation-reception__greeting";

function renderReception(
  displayName: string | null,
  isoNow = "2026-10-16T09:30:00",
) {
  vi.useFakeTimers();
  vi.setSystemTime(new Date(isoNow));
  return render(
    <DeliaReception
      userIdentity={{ displayName, imageUrl: null }}
    />,
  );
}

describe("DeliaReception — current user greeting", () => {
  it("greets by the canonical first-name projection at morning", () => {
    renderReception("Robério Oliveira", "2026-10-16T09:30:00");
    expect(document.querySelector(GREETING_SEL)?.textContent).toBe(
      "Bom dia, Robério.",
    );
  });

  it("uses Boa tarde / Boa noite deterministically", () => {
    const { unmount } = renderReception(
      "Robério Oliveira",
      "2026-10-16T14:00:00",
    );
    expect(document.querySelector(GREETING_SEL)?.textContent).toBe(
      "Boa tarde, Robério.",
    );
    unmount();
    renderReception("Robério Oliveira", "2026-10-16T20:00:00");
    expect(document.querySelector(GREETING_SEL)?.textContent).toBe(
      "Boa noite, Robério.",
    );
  });

  it("omits the greeting entirely when no name is available", () => {
    renderReception(null);
    expect(document.querySelector(GREETING_SEL)).toBeNull();
    expect(document.querySelector("h2")?.textContent).toBe(
      "Como posso ajudar você hoje?",
    );
  });

  it("omits the greeting for whitespace-only names — nothing invented", () => {
    renderReception("   ");
    expect(document.querySelector(GREETING_SEL)).toBeNull();
  });

  it("renders hostile display names as inert text", () => {
    renderReception('<img src=x onerror=alert(1)>"script"', "2026-10-16T10:00:00");
    const greeting = document.querySelector(GREETING_SEL);
    // Canonical first-token projection keeps the hostile text inert.
    expect(greeting?.textContent).toBe('Bom dia, <img.');
    expect(document.querySelector("img")).toBeNull();
    expect(document.querySelector("script")).toBeNull();
  });

  it("renders very long names without truncation/inference", () => {
    renderReception(
      "Maria Clara dos Santos Ferreira Albuquerque Cavalcanti",
      "2026-10-16T10:00:00",
    );
    expect(document.querySelector(GREETING_SEL)?.textContent).toBe(
      "Bom dia, Maria.",
    );
  });

  it("has no status/alert/live region — reception is static", () => {
    const { container } = renderReception("Robério Oliveira");
    expect(container.querySelector("[role=status]")).toBeNull();
    expect(container.querySelector("[role=alert]")).toBeNull();
    expect(container.querySelector("[aria-live]")).toBeNull();
  });

  it("keeps the DÉLIA avatar decorative with no user photo leak", () => {
    const { container } = renderReception("Robério Oliveira");
    const avatar = container.querySelector(
      ".delpi-ui-conversation-reception__avatar",
    );
    expect(avatar?.getAttribute("aria-hidden")).toBe("true");
    // The reception avatar is the assistant mark — never the user photo.
    expect(avatar?.querySelector("img")).toBeNull();
  });
});
