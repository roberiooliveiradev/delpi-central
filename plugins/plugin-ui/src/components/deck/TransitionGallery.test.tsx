import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TransitionGallery } from "./TransitionGallery";

afterEach(cleanup);

const OPTIONS = [
  { id: "", label: "Herdar", previewStyle: "fade" },
  { id: "fade", label: "Suavizar" },
  { id: "wipe", label: "Revelar" },
] as const;

describe("TransitionGallery", () => {
  it("marca a opção ativa e entrega o id selecionado", () => {
    const onChange = vi.fn();
    render(<TransitionGallery options={OPTIONS} value="fade" onChange={onChange} />);

    expect(screen.getByRole("option", { name: "Suavizar" }).getAttribute("aria-selected")).toBe(
      "true",
    );
    fireEvent.click(screen.getByRole("option", { name: "Revelar" }));
    expect(onChange).toHaveBeenCalledWith("wipe");
  });

  it("permite representar herança sem persistir um id artificial", () => {
    render(<TransitionGallery options={OPTIONS} value="" onChange={() => undefined} />);

    expect(screen.getByRole("option", { name: "Herdar" }).getAttribute("aria-selected")).toBe(
      "true",
    );
  });
});

