import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { BringToFront } from "lucide-react";

import { DeckRibbonMenuTile } from "./DeckRibbonMenuTile";

describe("DeckRibbonMenuTile", () => {
  it("dispara primary e abre menu com itens", () => {
    const onPrimary = vi.fn();
    const onFront = vi.fn();
    render(
      <DeckRibbonMenuTile
        icon={BringToFront}
        label="Avançar"
        onPrimaryClick={onPrimary}
        items={[
          { id: "forward", label: "Avançar", onSelect: onPrimary },
          { id: "front", label: "Trazer para a Frente", onSelect: onFront },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Avançar" }));
    expect(onPrimary).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Avançar: mais opções" }));
    expect(screen.getByRole("menuitem", { name: "Trazer para a Frente" })).toBeTruthy();
    fireEvent.click(screen.getByRole("menuitem", { name: "Trazer para a Frente" }));
    expect(onFront).toHaveBeenCalled();
  });
});
