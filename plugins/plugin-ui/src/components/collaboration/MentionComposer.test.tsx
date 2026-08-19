import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { useState, type ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MentionComposer, mentionComposerBemClasses } from "./MentionComposer";
import {
  detectActiveMention,
  insertMentionToken,
  replaceEditablePlainRange,
  snapshotEditablePlaintext,
} from "./mentionComposerCaret";
import type { MentionMenuHit } from "./MentionMenu";

const classNames = mentionComposerBemClasses("test");
const stylesDir = join(dirname(fileURLToPath(import.meta.url)), "../../styles");

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

  it("substitui intervalo plano no contenteditable", () => {
    const root = document.createElement("div");
    root.textContent = "Hi @An";
    document.body.appendChild(root);
    replaceEditablePlainRange(root, 3, 6, "@Ana ");
    expect(root.textContent).toBe("Hi @Ana ");
    root.remove();
  });
});

describe("MentionComposer", () => {
  function Harness({
    hits = [] as MentionMenuHit[],
    onSubmit = vi.fn(),
    onMentionQueryChange = vi.fn(),
    onFilesSelected,
    initial = "",
  }: {
    hits?: MentionMenuHit[];
    onSubmit?: () => void;
    onMentionQueryChange?: (q: string | null) => void;
    onFilesSelected?: (files: File[]) => void;
    initial?: string;
  }): ReactElement {
    const [value, setValue] = useState(initial);
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

  it("renderiza contenteditable markdown, não textarea nativo", () => {
    render(<Harness />);
    const surface = screen.getByLabelText("Write a message");
    expect(surface.tagName).toBe("DIV");
    expect(surface.getAttribute("contenteditable")).toBe("true");
    expect(screen.queryByRole("textbox", { name: "Write a message" })).toBe(surface);
    expect(screen.getByLabelText("Send")).toBeTruthy();
    expect(screen.getByLabelText("Attach")).toBeTruthy();
  });

  it("round-trip: markdown controlado vira HTML e o input devolve markdown", () => {
    const { rerender } = render(
      <MentionComposer
        value="**hi**"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        labels={labels}
        classNames={classNames}
      />,
    );
    const surface = screen.getByLabelText("Write a message");
    expect(surface.innerHTML.toLowerCase()).toContain("strong");

    const onChange = vi.fn();
    rerender(
      <MentionComposer
        value="**hi**"
        onChange={onChange}
        onSubmit={vi.fn()}
        labels={labels}
        classNames={classNames}
      />,
    );
    surface.innerHTML = "<p><strong>ok</strong></p>";
    fireEvent.input(surface);
    expect(onChange).toHaveBeenCalled();
    expect(String(onChange.mock.calls.at(-1)?.[0])).toMatch(/\*\*ok\*\*/);
  });

  it("opens mention query callback when typing @", () => {
    const onMentionQueryChange = vi.fn();
    render(<Harness onMentionQueryChange={onMentionQueryChange} />);
    const surface = screen.getByLabelText("Write a message");
    surface.textContent = "@An";
    const textNode = surface.firstChild as Text;
    const range = document.createRange();
    range.setStart(textNode, 3);
    range.collapse(true);
    const sel = window.getSelection();
    sel?.removeAllRanges();
    sel?.addRange(range);
    fireEvent.input(surface);
    expect(onMentionQueryChange).toHaveBeenCalledWith("An");
  });

  it("submits with Ctrl+Enter when not empty", () => {
    const onSubmit = vi.fn();
    render(<Harness onSubmit={onSubmit} initial="Hello" />);
    const surface = screen.getByLabelText("Write a message");
    fireEvent.keyDown(surface, { key: "Enter", ctrlKey: true });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("aplica atalho Ctrl+B via execCommand", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    render(<Harness initial="Hello" />);
    const surface = screen.getByLabelText("Write a message");
    fireEvent.keyDown(surface, { key: "b", ctrlKey: true });
    expect(document.execCommand).toHaveBeenCalledWith("bold", false, undefined);
  });

  it("inserts selected mention from the menu", () => {
    const hits: MentionMenuHit[] = [
      { id: "u1", kind: "user", label: "Ana", groupLabel: "People" },
    ];
    render(<Harness hits={hits} />);
    const surface = screen.getByLabelText("Write a message");
    surface.textContent = "Oi @A";
    const textNode = surface.firstChild as Text;
    const range = document.createRange();
    range.setStart(textNode, 5);
    range.collapse(true);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(range);
    fireEvent.input(surface);
    fireEvent.mouseDown(screen.getByRole("option", { name: /Ana/ }));
    expect(snapshotEditablePlaintext(surface).text).toMatch(/@Ana/);
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

describe("mention-composer.css", () => {
  it("pílula 1.25rem, focus em box-shadow e send circular 36px", () => {
    const css = readFileSync(join(stylesDir, "mention-composer.css"), "utf8");
    const body = css.match(/\.delpi-ui-mention-composer__body \{[^}]+\}/)?.[0] ?? "";
    const focus =
      css.match(/\.delpi-ui-mention-composer__body:focus-within \{[^}]+\}/)?.[0] ?? "";
    const sendBlocks = [
      ...(css.matchAll(/\.delpi-ui-mention-composer__send \{[^}]+\}/g) ?? []),
    ].map((match) => match[0]);
    expect(body).toMatch(/border-radius:\s*1\.25rem;/);
    expect(focus).toMatch(/box-shadow:/);
    expect(focus).not.toMatch(/outline:\s*2px/);
    expect(sendBlocks.join("\n")).toMatch(/width:\s*36px;/);
    expect(sendBlocks.join("\n")).toMatch(/border-radius:\s*50%;/);
    expect(css).toMatch(/\[contenteditable="false"\]/);
    expect(css).not.toMatch(/textarea::placeholder/);
  });
});
