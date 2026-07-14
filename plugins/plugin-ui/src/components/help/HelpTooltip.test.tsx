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

/** Componentes compostos não encaminham onMouseEnter — o wrap precisa ouvir no hit-target. */
function CompositeColorTrigger({ label }: { label: string }) {
  return (
    <div className="fake-color-picker">
      <button type="button" aria-expanded="false" aria-label={label}>
        Swatch
      </button>
    </div>
  );
}

describe("HelpTooltip", () => {
  it("mostra balão no hover do gatilho quando o menu está fechado", () => {
    const { container } = render(<ExpandableHint />);
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Ajuda do preenchimento",
    );
  });

  it("mostra balão no hover de componente composto (sem encaminhar props)", () => {
    const { container } = render(
      <HelpTooltip content="Cor do texto" wrap placement="bottom">
        <CompositeColorTrigger label="Cor texto" />
      </HelpTooltip>,
    );
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe("Cor do texto");
  });

  it("não mostra balão no hover quando aria-expanded=true", () => {
    const { container } = render(<ExpandableHint />);
    const trigger = within(container).getByRole("button", { name: "Preench." });
    fireEvent.click(trigger);
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });

  it("esconde o balão ao abrir o menu com o ponteiro ainda no botão", () => {
    const { container } = render(<ExpandableHint />);
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.getByRole("tooltip", { hidden: true })).toBeTruthy();
    fireEvent.click(within(container).getByRole("button", { name: "Preench." }));
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });

  it("respeita suppressed explícito", () => {
    const { container } = render(
      <HelpTooltip content="Ajuda" wrap suppressed>
        <button type="button">Gatilho</button>
      </HelpTooltip>,
    );
    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip")!);
    expect(screen.queryByRole("tooltip", { hidden: true })).toBeNull();
  });
});
