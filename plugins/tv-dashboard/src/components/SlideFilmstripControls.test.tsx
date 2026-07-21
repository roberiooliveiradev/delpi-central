import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SlideFilmstripControls } from "./SlideFilmstripControls";

afterEach(() => {
  cleanup();
});

describe("SlideFilmstripControls", () => {
  it("renderiza só Nova tela (sem nav de slides)", () => {
    const onAdd = vi.fn();
    render(<SlideFilmstripControls onAdd={onAdd} />);

    expect(screen.getByRole("button", { name: "Nova tela" })).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Trocar slide" })).toBeNull();
    expect(screen.queryByText(/\d+\s*\/\s*\d+/)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Nova tela" }));
    expect(onAdd).toHaveBeenCalledTimes(1);
  });
});
