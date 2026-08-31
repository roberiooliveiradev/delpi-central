import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useRef, type ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  MentionMenu,
  groupMentionMenuHits,
  mentionMenuBemClasses,
  type MentionMenuHit,
} from "./MentionMenu";

const classNames = mentionMenuBemClasses("test");

const hits: MentionMenuHit[] = [
  {
    id: "u1",
    kind: "user",
    label: "Ana Silva",
    subtitle: "ana@delpi",
    groupLabel: "People",
  },
  {
    id: "o1",
    kind: "order",
    label: "102942",
    subtitle: "ACME",
    groupLabel: "Objects",
  },
];

function Harness({
  open = true,
  items = hits,
  onSelect = vi.fn(),
  onDismiss = vi.fn(),
}: {
  open?: boolean;
  items?: MentionMenuHit[];
  onSelect?: (hit: MentionMenuHit) => void;
  onDismiss?: () => void;
}): ReactElement {
  const anchorRef = useRef<HTMLButtonElement>(null);
  return (
    <>
      <button ref={anchorRef} type="button">
        anchor
      </button>
      <MentionMenu
        open={open}
        anchorRef={anchorRef}
        hits={items}
        classNames={classNames}
        listAriaLabel="Mentions"
        emptyLabel="No results"
        onSelect={onSelect}
        onDismiss={onDismiss}
      />
    </>
  );
}

afterEach(() => {
  cleanup();
});

describe("groupMentionMenuHits", () => {
  it("preserves first-seen group order", () => {
    const groups = groupMentionMenuHits(hits);
    expect(groups.map((g) => g.groupLabel)).toEqual(["People", "Objects"]);
    expect(groups[0]?.items).toHaveLength(1);
  });
});

describe("MentionMenu", () => {
  it("renders grouped options", () => {
    render(<Harness />);
    expect(screen.getByText("People")).toBeTruthy();
    expect(screen.getByText("Objects")).toBeTruthy();
    expect(screen.getByRole("option", { name: /Ana Silva/ })).toBeTruthy();
    expect(screen.getByRole("option", { name: /102942/ })).toBeTruthy();
  });

  it("renders avatar when hit provides avatarName", () => {
    const { container } = render(
      <Harness
        items={[
          {
            id: "u1",
            kind: "user",
            label: "Ana Silva",
            avatarName: "Ana Silva",
            avatarSrc: "https://cdn.example/ana.png",
          },
        ]}
      />,
    );
    const option = screen.getByRole("option", { name: /Ana Silva/ });
    const img = option.querySelector("img");
    expect(img?.getAttribute("src")).toBe("https://cdn.example/ana.png");
  });

  it("shows empty label when there are no hits", () => {
    render(<Harness items={[]} />);
    expect(screen.getByRole("status").textContent).toBe("No results");
  });

  it("selects with Enter on the active option", () => {
    const onSelect = vi.fn();
    render(<Harness onSelect={onSelect} />);
    fireEvent.keyDown(window, { key: "ArrowDown" });
    fireEvent.keyDown(window, { key: "Enter" });
    expect(onSelect).toHaveBeenCalledTimes(1);
    expect(onSelect.mock.calls[0]?.[0]?.id).toBe("o1");
  });

  it("selects on mouse down", () => {
    const onSelect = vi.fn();
    render(<Harness onSelect={onSelect} />);
    fireEvent.mouseDown(screen.getByRole("option", { name: /Ana Silva/ }));
    expect(onSelect.mock.calls[0]?.[0]?.id).toBe("u1");
  });
});
