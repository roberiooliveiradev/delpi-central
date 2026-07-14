import { render } from "@testing-library/react";
import { useRef, useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { useClickOutside } from "./useClickOutside";

function Probe({
  onOutside,
  nestedModal,
}: {
  onOutside: () => void;
  nestedModal?: boolean;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [open] = useState(true);
  useClickOutside([rootRef, panelRef], open, onOutside);

  return (
    <div>
      <div ref={rootRef} data-testid="root">
        trigger
      </div>
      <div ref={panelRef} data-testid="panel">
        panel
      </div>
      {nestedModal ? (
        <div role="dialog" aria-modal="true" data-testid="nested-modal">
          <button type="button">swatch</button>
        </div>
      ) : null}
    </div>
  );
}

describe("useClickOutside", () => {
  it("ignora clique dentro de modal aninhado com aria-modal", () => {
    const onOutside = vi.fn();
    render(<Probe onOutside={onOutside} nestedModal />);

    const button = document.querySelector('[data-testid="nested-modal"] button');
    expect(button).toBeTruthy();
    button!.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));

    expect(onOutside).not.toHaveBeenCalled();
  });

  it("dispara ao clicar fora do painel e do modal", () => {
    const onOutside = vi.fn();
    render(<Probe onOutside={onOutside} nestedModal />);

    document.body.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));

    expect(onOutside).toHaveBeenCalledTimes(1);
  });

  it("dispara na captura mesmo com stopPropagation no alvo", () => {
    const onOutside = vi.fn();
    render(
      <div>
        <Probe onOutside={onOutside} />
        <button
          type="button"
          data-testid="blocked"
          onPointerDown={(event) => event.stopPropagation()}
        >
          blocked
        </button>
      </div>,
    );

    const blocked = document.querySelector('[data-testid="blocked"]');
    expect(blocked).toBeTruthy();
    blocked!.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true }));

    expect(onOutside).toHaveBeenCalledTimes(1);
  });

  it("ignora clique em portal aninhado (.delpi-ui-select__panel)", () => {
    const onOutside = vi.fn();
    render(
      <div>
        <Probe onOutside={onOutside} />
        <div className="delpi-ui-select__panel" data-testid="nested-select">
          <button type="button">opção</button>
        </div>
      </div>,
    );

    document
      .querySelector('[data-testid="nested-select"] button')!
      .dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));

    expect(onOutside).not.toHaveBeenCalled();
  });

  it("não dispara ao clicar no painel", () => {
    const onOutside = vi.fn();
    render(<Probe onOutside={onOutside} />);

    document
      .querySelector('[data-testid="panel"]')!
      .dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));

    expect(onOutside).not.toHaveBeenCalled();
  });
});
