import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { StatusBadge } from "./StatusBadge";

afterEach(() => {
  cleanup();
});

describe("StatusBadge", () => {
  it.each([
    ["pending", "Aguardando lançamento"],
    ["in_progress", "Em atendimento"],
    ["blocked", "Com pendência"],
    ["posted", "Lançada"],
    ["cancelled", "Cancelada"],
  ] as const)("renderiza %s", (status, label) => {
    render(<StatusBadge status={status} />);
    const badge = screen.getByTestId("status-badge");
    expect(badge.textContent).toContain(label);
    expect(badge.getAttribute("data-status")).toBe(status);
  });
});
