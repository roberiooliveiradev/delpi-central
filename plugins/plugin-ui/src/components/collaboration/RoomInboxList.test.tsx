import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RoomInboxList, roomInboxListBemClasses } from "./RoomInboxList";

const classNames = roomInboxListBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

afterEach(() => {
  cleanup();
});

describe("RoomInboxList", () => {
  it("renders empty state", () => {
    render(
      <RoomInboxList
        classNames={classNames}
        items={[]}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
      />,
    );
    expect(screen.getByRole("status").textContent).toBe("No rooms");
  });

  it("selects a room and shows unread badge", () => {
    const onSelect = vi.fn();
    render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        unreadBadgeLabel={(n) => `${n} unread`}
        onSelect={onSelect}
        items={[
          {
            id: "r1",
            title: "Pedido 102942",
            preview: "Atualização",
            unreadCount: 2,
            kindLabel: "Entity",
          },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /Pedido 102942/ }));
    expect(onSelect).toHaveBeenCalledWith("r1");
    expect(screen.getByText("2 unread")).toBeTruthy();
  });

  it("renders leading and subtitle slots", () => {
    render(
      <RoomInboxList
        classNames={classNames}
        listAriaLabel="Inbox"
        emptyLabel="No rooms"
        leading={() => <span>AV</span>}
        subtitle={(item) => `Cliente ${item.title}`}
        items={[
          {
            id: "r1",
            title: "Pedido 102942",
            preview: "Atualização",
            selected: true,
          },
        ]}
      />,
    );
    expect(screen.getByText("AV")).toBeTruthy();
    expect(screen.getByText("Cliente Pedido 102942")).toBeTruthy();
    expect(screen.getByRole("button").getAttribute("aria-current")).toBe("true");
  });
});

describe("room-inbox.css", () => {
  it("seleção usa barra 3px e fill, sem borda full", () => {
    const css = readFileSync(join(stylesDir, "room-inbox.css"), "utf8");
    const item = css.match(/\.delpi-ui-room-inbox__item \{[^}]+\}/)?.[0] ?? "";
    const selected =
      css.match(/\.delpi-ui-room-inbox__item--selected \{[^}]+\}/)?.[0] ?? "";
    expect(item).toMatch(/border:\s*none;/);
    expect(item).not.toMatch(/border:\s*1px solid/);
    expect(selected).toMatch(/inset 3px 0 0/);
    expect(selected).not.toMatch(/border-color:/);
  });
});
