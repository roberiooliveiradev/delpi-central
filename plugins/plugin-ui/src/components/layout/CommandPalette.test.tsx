import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CommandPalette, commandPaletteBemClasses } from "./CommandPalette";

afterEach(() => {
  cleanup();
});

describe("CommandPalette", () => {
  it("abre popover ancorado e seleciona hit", () => {
    const onSelectHit = vi.fn();
    const onClose = vi.fn();
    const onChange = vi.fn();
    const anchorRef = createRef<HTMLButtonElement>();

    render(
      <div className="dashboard-commercial">
        <button type="button" ref={anchorRef}>
          Buscar
        </button>
        <CommandPalette
          open
          onClose={onClose}
          title="Buscar"
          anchorRef={anchorRef}
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
    expect(document.querySelector(".delpi-ui-command-palette")).toBeTruthy();
    expect(document.querySelector(".delpi-ui-modal")).toBeNull();
    const input = screen.getByRole("combobox");
    fireEvent.focus(input);
    fireEvent.click(screen.getByRole("option", { name: /Propostas/ }));
    expect(onSelectHit).toHaveBeenCalledWith("proposals");
    expect(onClose).toHaveBeenCalled();
  });
});
