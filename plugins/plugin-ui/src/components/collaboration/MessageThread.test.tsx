import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MessageThread, messageThreadBemClasses } from "./MessageThread";

const classNames = messageThreadBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("MessageThread", () => {
  it("shows empty state", () => {
    render(
      <MessageThread
        classNames={classNames}
        messages={[]}
        listAriaLabel="Messages"
        emptyLabel="No messages yet"
      />,
    );
    expect(screen.getByRole("status").textContent).toBe("No messages yet");
  });

  it("renders text bubbles and system lines with reply indent", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hello @Ana",
            authorName: "Bruno",
            createdAtLabel: "10:00",
            mentions: [{ kind: "user", label: "@Ana" }],
          },
          {
            id: "2",
            kind: "system",
            bodyText: "Room created",
            createdAtLabel: "10:01",
          },
          {
            id: "3",
            kind: "text",
            bodyText: "Reply",
            authorName: "Ana",
            createdAtLabel: "10:02",
            parentId: "1",
          },
        ]}
      />,
    );
    expect(screen.getByText("Bruno")).toBeTruthy();
    expect(screen.getByText("Room created")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-message-thread__item--reply")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-mention-text__chip")).not.toBeNull();
  });

  it("exposes host actions on bubbles", () => {
    const onDelete = vi.fn();
    render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Hi",
            authorName: "Bruno",
            createdAtLabel: "10:00",
          },
        ]}
        resolveActions={() => [
          { id: "delete", label: "Delete", onClick: onDelete, danger: true },
        ]}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });
});
