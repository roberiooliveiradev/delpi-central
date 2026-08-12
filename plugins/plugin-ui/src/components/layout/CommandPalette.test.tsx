import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CommandPalette, commandPaletteBemClasses } from "./CommandPalette";

afterEach(() => {
  cleanup();
});

describe("CommandPalette", () => {
  it("abre dialog e seleciona hit", () => {
    const onSelectHit = vi.fn();
    const onClose = vi.fn();
    const onChange = vi.fn();
    render(
      <div className="dashboard-commercial">
        <CommandPalette
          open
          onClose={onClose}
          title="Buscar"
          value="pro"
          onChange={onChange}
          onSelectHit={onSelectHit}
          hits={[{ id: "proposals", label: "Propostas", groupLabel: "Documentos" }]}
          classNames={commandPaletteBemClasses("cm")}
          portalScopeClassName="dashboard-commercial"
        />
      </div>,
    );

    expect(screen.getByRole("dialog", { name: "Buscar" })).toBeTruthy();
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.click(screen.getByRole("option", { name: /Propostas/ }));
    expect(onSelectHit).toHaveBeenCalledWith("proposals");
    expect(onClose).toHaveBeenCalled();
  });
});
