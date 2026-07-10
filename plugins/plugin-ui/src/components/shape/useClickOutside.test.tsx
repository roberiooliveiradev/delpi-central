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
    button!.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));

    expect(onOutside).not.toHaveBeenCalled();
  });

  it("dispara ao clicar fora do painel e do modal", () => {
    const onOutside = vi.fn();
    render(<Probe onOutside={onOutside} nestedModal />);

    document.body.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));

    expect(onOutside).toHaveBeenCalledTimes(1);
  });
});
