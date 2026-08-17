import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("mostra rótulo de aguardando", () => {
    render(<StatusBadge status="pending" />);
    expect(screen.getByTestId("status-badge").textContent).toContain("Aguardando");
  });
});
