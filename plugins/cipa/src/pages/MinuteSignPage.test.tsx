// @vitest-environment jsdom

import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";

import { MinuteSignPage } from "./MinuteSignPage";

const api = vi.hoisted(() => ({
  getSignContext: vi.fn(),
  getMySignatureProfile: vi.fn(),
}));

vi.mock("../api/cipaApi", () => ({
  fetchMySignatureImageBlob: vi.fn(),
  getMySignatureProfile: api.getMySignatureProfile,
  getSignContext: api.getSignContext,
  getSignatureImage: vi.fn(),
  refuseMinute: vi.fn(),
  signMinute: vi.fn(),
}));

vi.mock("../hooks/useCipaRouterPath", () => ({
  navigateCipa: vi.fn(),
}));

const scrolledElements: Element[] = [];

beforeAll(() => {
  Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
    configurable: true,
    value: vi.fn(() => ({
      beginPath: vi.fn(),
      fillRect: vi.fn(),
      lineTo: vi.fn(),
      moveTo: vi.fn(),
      stroke: vi.fn(),
    })),
  });
  Object.defineProperty(Element.prototype, "scrollIntoView", {
    configurable: true,
    value: function scrollIntoView(this: Element) {
      scrolledElements.push(this);
    },
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  scrolledElements.length = 0;
});

describe("MinuteSignPage", () => {
  it("rola até o ponto de assinatura quando o contexto carrega", async () => {
    api.getSignContext.mockResolvedValue({
      minute: { id: "minute-1", minute_number: "ATA-001", title: "Reunião ordinária" },
      version: { body_html: "<p>Conteúdo da ata</p>", meeting_date: "2026-07-01" },
      participants: [],
      signers: [],
      signatures: [],
      terms: "Declaro que li a ata.",
    });
    api.getMySignatureProfile.mockResolvedValue(null);

    render(<MinuteSignPage unitCode="01" minuteId="minute-1" />);

    await screen.findByRole("button", { name: "Confirmar assinatura" });
    await waitFor(() =>
      expect(
        scrolledElements.some((element) =>
          element.classList.contains("cipa-sign-anchor"),
        ),
      ).toBe(true),
    );
  });
});
