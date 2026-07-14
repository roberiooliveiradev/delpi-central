import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useRef, useState } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { AnchoredPanelPortal } from "./AnchoredPanelPortal";
import { resetExclusiveAnchoredPanelForTests } from "./exclusiveAnchoredPanel";

afterEach(() => {
  cleanup();
  resetExclusiveAnchoredPanelForTests();
});

beforeEach(() => {
  resetExclusiveAnchoredPanelForTests();
});

function Menu({ label }: { label: string }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  return (
    <div ref={rootRef}>
      <button type="button" aria-expanded={open} onClick={() => setOpen((prev) => !prev)}>
        {label}
      </button>
      {open ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          role="menu"
          aria-label={label}
          onDismiss={() => setOpen(false)}
        >
          <div>{label} panel</div>
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

describe("AnchoredPanelPortal exclusive", () => {
  it("fecha o popover anterior ao abrir outro", () => {
    render(
      <>
        <Menu label="Preench." />
        <Menu label="Contorno" />
      </>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Preench." }));
    expect(screen.getByRole("menu", { name: "Preench." })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Contorno" }));
    expect(screen.queryByRole("menu", { name: "Preench." })).toBeNull();
    expect(screen.getByRole("menu", { name: "Contorno" })).toBeTruthy();
  });

  it("não fecha o pai quando o filho usa exclusive=false", () => {
    function Nested() {
      const [parentOpen, setParentOpen] = useState(false);
      const [childOpen, setChildOpen] = useState(false);
      const parentAnchor = useRef<HTMLDivElement>(null);
      const parentPanel = useRef<HTMLDivElement>(null);
      const childAnchor = useRef<HTMLDivElement>(null);
      const childPanel = useRef<HTMLDivElement>(null);

      return (
        <div ref={parentAnchor}>
          <button type="button" onClick={() => setParentOpen(true)}>
            Pai
          </button>
          {parentOpen ? (
            <AnchoredPanelPortal
              open={parentOpen}
              anchorRef={parentAnchor}
              panelRef={parentPanel}
              role="dialog"
              aria-label="Pai"
              onDismiss={() => setParentOpen(false)}
            >
              <div ref={childAnchor}>
                <button type="button" onClick={() => setChildOpen(true)}>
                  Filho
                </button>
                {childOpen ? (
                  <AnchoredPanelPortal
                    open={childOpen}
                    anchorRef={childAnchor}
                    panelRef={childPanel}
                    role="listbox"
                    aria-label="Filho"
                    exclusive={false}
                    onDismiss={() => setChildOpen(false)}
                  >
                    <div>filho panel</div>
                  </AnchoredPanelPortal>
                ) : null}
              </div>
            </AnchoredPanelPortal>
          ) : null}
        </div>
      );
    }

    render(<Nested />);
    fireEvent.click(screen.getByRole("button", { name: "Pai" }));
    fireEvent.click(screen.getByRole("button", { name: "Filho" }));

    expect(screen.getByRole("dialog", { name: "Pai" })).toBeTruthy();
    expect(screen.getByRole("listbox", { name: "Filho" })).toBeTruthy();
  });
});
