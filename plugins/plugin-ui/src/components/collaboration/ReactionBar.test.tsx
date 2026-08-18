import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReactionBar, reactionBarBemClasses } from "./ReactionBar";

const classNames = reactionBarBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("ReactionBar", () => {
  it("toggles existing reactions and adds available codes", () => {
    const onToggle = vi.fn();
    const onAdd = vi.fn();
    render(
      <ReactionBar
        classNames={classNames}
        listAriaLabel="Reactions"
        addAriaLabel="Add reaction"
        items={[{ code: "thumbsup", label: "👍", count: 2, reactedByMe: true }]}
        availableCodes={[
          { code: "thumbsup", label: "👍" },
          { code: "heart", label: "❤️" },
        ]}
        onToggle={onToggle}
        onAdd={onAdd}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "👍" }));
    expect(onToggle).toHaveBeenCalledWith("thumbsup");
    fireEvent.click(screen.getByRole("button", { name: "Add reaction: ❤️" }));
    expect(onAdd).toHaveBeenCalledWith("heart");
  });
});
