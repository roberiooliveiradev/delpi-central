import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { HelpTooltip } from "./HelpTooltip";

afterEach(() => {
  cleanup();
});

function ExpandableHint() {
  const [open, setOpen] = useState(false);
  return (
    <HelpTooltip content="Ajuda do preenchimento" wrap placement="bottom">
      <div>
        <button type="button" aria-expanded={open} onClick={() => setOpen(true)}>
          Preench.
        </button>
      </div>
    </HelpTooltip>
  );
}

describe("HelpTooltip", () => {
  it("mostra balão no hover do gatilho quando o menu está fechado", () => {
    const { container } = render(<ExpandableHint />);
    fireEvent.mouseEnter(within(container).getByRole("button", { name: "Preench." }));
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Ajuda do preenchimento",
    );
  });

  it("não mostra balão no hover quando aria-expanded=true", () => {
    const { container } = render(<ExpandableHint />);
    const trigger = within(container).getByRole("button", { name: "Preench." });
    fireEvent.click(trigger);
    fireEvent.mouseEnter(trigger);
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });

  it("esconde o balão ao abrir o menu com o ponteiro ainda no botão", () => {
    const { container } = render(<ExpandableHint />);
    const trigger = within(container).getByRole("button", { name: "Preench." });
    fireEvent.mouseEnter(trigger);
    expect(screen.getByRole("tooltip", { hidden: true })).toBeTruthy();
    fireEvent.click(trigger);
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });

  it("respeita suppressed explícito", () => {
    const { container } = render(
      <HelpTooltip content="Ajuda" wrap suppressed>
        <button type="button">Gatilho</button>
      </HelpTooltip>,
    );
    fireEvent.mouseEnter(within(container).getByRole("button", { name: "Gatilho" }));
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });
});
