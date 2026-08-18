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
});
