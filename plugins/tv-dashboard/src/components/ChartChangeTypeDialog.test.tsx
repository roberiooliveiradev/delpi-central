import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ChartChangeTypeDialog } from "./ChartChangeTypeDialog";

let host: HTMLElement;

beforeEach(() => {
  host = document.createElement("main");
  host.className = "dashboard-tv-dashboard";
  document.body.appendChild(host);
});

afterEach(() => {
  cleanup();
  host.remove();
});

describe("ChartChangeTypeDialog", () => {
  it("mostra Barras e Colunas como opções distintas em Comparação", () => {
    render(
      <ChartChangeTypeDialog
        open
        currentType="bar"
        onClose={() => undefined}
        onConfirm={() => undefined}
      />,
      { container: host },
    );
    expect(screen.getByRole("option", { name: "Colunas" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Barras" })).toBeTruthy();
  });

  it("confirma o tipo Barras escolhido", () => {
    const onConfirm = vi.fn();
    render(
      <ChartChangeTypeDialog
        open
        currentType="bar"
        onClose={() => undefined}
        onConfirm={onConfirm}
      />,
      { container: host },
    );
    fireEvent.click(screen.getByRole("option", { name: "Barras" }));
    fireEvent.click(screen.getByRole("button", { name: "OK" }));
    expect(onConfirm).toHaveBeenCalledWith("horizontal_bar");
  });
});
