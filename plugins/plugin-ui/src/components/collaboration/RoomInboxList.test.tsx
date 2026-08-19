import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RoomInboxList, roomInboxListBemClasses } from "./RoomInboxList";

const classNames = roomInboxListBemClasses("test");

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
