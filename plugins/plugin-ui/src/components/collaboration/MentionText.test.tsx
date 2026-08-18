import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MentionText, mentionTextBemClasses } from "./MentionText";

const classNames = mentionTextBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("MentionText", () => {
  it("renders chips for bare mentions without @ in the label text", () => {
    const { container } = render(
      <MentionText classNames={classNames} text="Oi @Ana" />,
    );
    expect(container.textContent).toBe("Oi Ana");
    expect(container.querySelector(".delpi-ui-mention-text__chip")).not.toBeNull();
  });

  it("renders structured mention as link when href is safe", () => {
    render(
      <MentionText
        classNames={classNames}
        text="Ver @Ana"
        mentions={[
          {
            kind: "user",
            label: "@Ana",
            href: "/apps/commercial/users/u1",
            title: "Abrir Ana",
          },
        ]}
      />,
    );
    const link = screen.getByRole("link", { name: "Ana" });
    expect(link.getAttribute("href")).toBe("/apps/commercial/users/u1");
    expect(link.getAttribute("data-mention-kind")).toBe("user");
  });

  it("calls onMentionActivate for button chips", () => {
    const onActivate = vi.fn();
    const item = { kind: "user", label: "@Ana", id: "u1" };
    render(
      <MentionText
        classNames={classNames}
        text="Oi @Ana"
        mentions={[item]}
        onMentionActivate={onActivate}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ana" }));
    expect(onActivate).toHaveBeenCalledTimes(1);
    expect(onActivate.mock.calls[0]?.[0]).toEqual(item);
  });
});
