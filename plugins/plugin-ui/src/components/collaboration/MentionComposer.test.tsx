import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState, type ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MentionComposer, mentionComposerBemClasses } from "./MentionComposer";
import {
  detectActiveMention,
  insertMentionToken,
} from "./mentionComposerCaret";
import type { MentionMenuHit } from "./MentionMenu";

const classNames = mentionComposerBemClasses("test");

const labels = {
  placeholder: "Write a message",
  sendAriaLabel: "Send",
  attachAriaLabel: "Attach",
  mentionListAriaLabel: "Mentions",
  mentionEmptyLabel: "No matches",
};

afterEach(() => {
  cleanup();
});

describe("mentionComposerCaret", () => {
  it("detects @query at caret", () => {
    expect(detectActiveMention("Hi @An", 6)).toEqual({
      query: "An",
      start: 3,
      end: 6,
    });
  });

  it("inserts mention token and advances caret", () => {
    const result = insertMentionToken("Hi @An", 6, 3, "Ana Silva");
    expect(result.token).toBe("@Ana Silva");
    expect(result.nextValue).toBe("Hi @Ana Silva ");
    expect(result.nextCursor).toBe("Hi @Ana Silva ".length);
  });
});

describe("MentionComposer", () => {
  function Harness({
    hits = [] as MentionMenuHit[],
    onSubmit = vi.fn(),
    onMentionQueryChange = vi.fn(),
    onFilesSelected,
  }: {
    hits?: MentionMenuHit[];
    onSubmit?: () => void;
    onMentionQueryChange?: (q: string | null) => void;
    onFilesSelected?: (files: File[]) => void;
  }): ReactElement {
    const [value, setValue] = useState("");
    return (
      <MentionComposer
        value={value}
        onChange={setValue}
        onSubmit={onSubmit}
        labels={labels}
        classNames={classNames}
        mentionHits={hits}
        onMentionQueryChange={onMentionQueryChange}
        showAttach
        onFilesSelected={onFilesSelected}
      />
    );
  }

  it("renders textarea and send/attach inside the kit", () => {
    render(<Harness />);
    expect(screen.getByLabelText("Write a message").tagName).toBe("TEXTAREA");
    expect(screen.getByLabelText("Send")).toBeTruthy();
    expect(screen.getByLabelText("Attach")).toBeTruthy();
  });

  it("opens mention query callback when typing @", () => {
    const onMentionQueryChange = vi.fn();
    render(<Harness onMentionQueryChange={onMentionQueryChange} />);
    const area = screen.getByLabelText("Write a message");
    fireEvent.change(area, { target: { value: "@An", selectionStart: 3 } });
    expect(onMentionQueryChange).toHaveBeenCalledWith("An");
  });

  it("submits with Ctrl+Enter when not empty", () => {
    const onSubmit = vi.fn();
    render(<Harness onSubmit={onSubmit} />);
    const area = screen.getByLabelText("Write a message");
    fireEvent.change(area, { target: { value: "Hello" } });
    fireEvent.keyDown(area, { key: "Enter", ctrlKey: true });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("inserts selected mention from the menu", () => {
    const hits: MentionMenuHit[] = [
      { id: "u1", kind: "user", label: "Ana", groupLabel: "People" },
    ];
    render(<Harness hits={hits} />);
    const area = screen.getByLabelText("Write a message") as HTMLTextAreaElement;
    fireEvent.change(area, { target: { value: "Oi @A", selectionStart: 5 } });
    fireEvent.mouseDown(screen.getByRole("option", { name: /Ana/ }));
    expect(area.value).toMatch(/@Ana/);
  });

  it("opens the hidden file input when attach is clicked", () => {
    const onFilesSelected = vi.fn();
    const { container } = render(<Harness onFilesSelected={onFilesSelected} />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input).toBeTruthy();
    const click = vi.spyOn(input, "click");
    fireEvent.click(screen.getByLabelText("Attach"));
    expect(click).toHaveBeenCalledTimes(1);
    const file = new File(["x"], "note.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file] } });
    expect(onFilesSelected).toHaveBeenCalledTimes(1);
    expect(onFilesSelected.mock.calls[0]?.[0]?.[0]?.name).toBe("note.pdf");
  });
});
