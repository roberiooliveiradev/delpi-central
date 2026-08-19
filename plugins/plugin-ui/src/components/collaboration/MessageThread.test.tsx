import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MessageThread, messageThreadBemClasses } from "./MessageThread";

const classNames = messageThreadBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

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
    expect(container.querySelector('[data-message-id="1"]')).not.toBeNull();
    expect(container.querySelector('[data-message-id="2"]')).not.toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__item--reply")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-mention-text__chip")).not.toBeNull();
  });

  it("aligns mine bubbles to the right without system avatar", () => {
    const { container } = render(
      <MessageThread
        classNames={classNames}
        listAriaLabel="Messages"
        emptyLabel="Empty"
        messages={[
          {
            id: "1",
            kind: "text",
            bodyText: "Mine",
            authorName: "Eu",
            createdAtLabel: "10:00",
            mine: true,
          },
          {
            id: "2",
            kind: "system",
            bodyText: "Pinned",
            createdAtLabel: "10:01",
            mine: true,
          },
        ]}
      />,
    );
    expect(container.querySelector(".delpi-ui-message-thread__item--mine")).not.toBeNull();
    expect(container.querySelector(".delpi-ui-message-thread__bubble--mine")).not.toBeNull();
    expect(
      container.querySelector('[data-message-kind="system"] .delpi-ui-avatar'),
    ).toBeNull();
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

  it("exposes icon actions by accessible name without permanent text", () => {
    const onPin = vi.fn();
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
          {
            id: "pin",
            label: "Pin message",
            title: "Pin message",
            icon: <span>📌</span>,
            onClick: onPin,
          },
        ]}
      />,
    );
    expect(screen.queryByText("Pin message")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Pin message" }));
    expect(onPin).toHaveBeenCalledTimes(1);
  });
});

describe("message-thread.css host scroll", () => {
  it("rola no host: lista overflow visible e teto na bolha", () => {
    const css = readFileSync(join(stylesDir, "message-thread.css"), "utf8");
    const root = css.match(/\.delpi-ui-message-thread \{[^}]+\}/)?.[0] ?? "";
    const row = css.match(/\.delpi-ui-message-thread__row \{[^}]+\}/)?.[0] ?? "";
    const bubble = css.match(/\.delpi-ui-message-thread__bubble \{[^}]+\}/)?.[0] ?? "";
    expect(root).toMatch(/overflow:\s*visible;/);
    expect(root).not.toMatch(/overflow-y:\s*auto;/);
    expect(row).toMatch(/max-width:\s*none;/);
    expect(row).not.toMatch(/min\(75%/);
    expect(bubble).toMatch(/max-width:\s*min\(75%,\s*42rem\)/);
  });
});
