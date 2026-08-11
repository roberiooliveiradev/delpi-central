import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
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

  it("usa tokens do kit para superfície, texto e seleção", () => {
    const css = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../../styles/transition-gallery.css"),
      "utf8",
    );

    expect(css).toContain("--delpi-ui-surface");
    expect(css).toContain("--delpi-ui-text");
    expect(css).toContain("--delpi-ui-accent");
    expect(css).toContain("__item--active");
    expect(css).not.toMatch(/background:\s*var\(--delpi-surface/);
    expect(css).not.toContain("--delpi-primary");
  });
});

