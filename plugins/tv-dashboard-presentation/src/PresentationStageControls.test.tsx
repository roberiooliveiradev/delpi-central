import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PresentationStageControls } from "./PresentationStageControls";

afterEach(() => {
  cleanup();
});

describe("PresentationStageControls", () => {
  it("abre menu customizado de seções e salta ao clicar", () => {
    const onJump = vi.fn();
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        sections={[
          { id: "main", name: "Principal", sortOrder: 0, isMain: true },
          { id: "sec-b", name: "Produção", sortOrder: 1 },
        ]}
        onJumpToSection={onJump}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Ir para seção" }));
    expect(screen.getByRole("listbox", { name: "Seções" })).toBeTruthy();
    fireEvent.click(screen.getByRole("option", { name: "Produção" }));
    expect(onJump).toHaveBeenCalledWith("sec-b");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("não mostra salto quando só existe a seção principal", () => {
    render(
      <PresentationStageControls
        index={0}
        total={1}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        sections={[{ id: "main", name: "Principal", sortOrder: 0, isMain: true }]}
        onJumpToSection={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Ir para seção" })).toBeNull();
  });
});
