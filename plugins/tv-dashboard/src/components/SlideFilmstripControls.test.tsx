import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Slide } from "../api/tvDashboardApi";
import { SlideFilmstripControls } from "./SlideFilmstripControls";

afterEach(() => {
  cleanup();
});

const slides = [
  { id: "a", title: "Um" },
  { id: "b", title: "Dois" },
] as Slide[];

describe("SlideFilmstripControls", () => {
  it("renderiza Nova tela e navegação acima das prévias (contador)", () => {
    const onAdd = vi.fn();
    const onSelect = vi.fn();
    render(
      <SlideFilmstripControls
        slides={slides}
        selectedSlideId="a"
        onAdd={onAdd}
        onSelect={onSelect}
      />,
    );

    expect(screen.getByRole("button", { name: "Nova tela" })).toBeTruthy();
    expect(screen.getByText("1 / 2")).toBeTruthy();
    expect(screen.getByRole("group", { name: "Trocar slide" })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Nova tela" }));
    expect(onAdd).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Próximo slide" }));
    expect(onSelect).toHaveBeenCalledWith("b");
  });
});
