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
    const { container } = render(<Harness />);
    const surface = screen.getByLabelText("Write a message");
    expect(surface.tagName).toBe("DIV");
    expect(surface.getAttribute("contenteditable")).toBe("true");
    expect(screen.queryByRole("textbox", { name: "Write a message" })).toBe(surface);
    expect(screen.getByLabelText("Send")).toBeTruthy();
    expect(screen.getByLabelText("Attach")).toBeTruthy();
    expect(surface.textContent ?? "").toBe("");
    expect(surface.getAttribute("data-placeholder")).toBeNull();
    expect(surface.getAttribute("aria-placeholder")).toBe("Write a message");
    const overlay = container.querySelector("[class*='placeholder']");
    expect(overlay?.textContent).toBe("Write a message");
    fireEvent.focus(surface);
    const range = window.getSelection()?.getRangeAt(0);
    expect(range?.collapsed).toBe(true);
    expect(range?.startOffset).toBe(0);
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

  it("Enter envia e Shift+Enter não envia", () => {
    const onSubmit = vi.fn();
    render(<Harness onSubmit={onSubmit} initial="Hello" />);
    const surface = screen.getByLabelText("Write a message");
    fireEvent.keyDown(surface, { key: "Enter", shiftKey: true });
    expect(onSubmit).not.toHaveBeenCalled();
    fireEvent.keyDown(surface, { key: "Enter" });
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("aplica Ctrl+B envolvendo o texto em strong", () => {
    render(<Harness initial="Hello" />);
    const surface = screen.getByLabelText("Write a message");
    fireEvent.keyDown(surface, { key: "b", ctrlKey: true });
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
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

  it("abre Formatar, aplica negrito e sanitiza HTML colado sem toolbar de deck", () => {
    const source = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "MentionComposer.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/from ["'][^"']*RichTextToolbar["']/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextEditor["']/);
    expect(source).not.toMatch(/<RichTextToolbar|<RichTextEditor/);
    expect(source).toMatch(/HintAction/);

    document.execCommand = vi.fn().mockReturnValue(true);
    const formatLabels = {
      ...labels,
      formatToggleAriaLabel: "Format",
      formatBoldAriaLabel: "Bold",
      formatFontSizeAriaLabel: "Font size",
      formatFontSizeDecreaseAriaLabel: "Decrease font size",
      formatFontSizeIncreaseAriaLabel: "Increase font size",
    };
    const { container } = render(
      <MentionComposer
        value="dsdssssdsds"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        labels={formatLabels}
        classNames={classNames}
      />,
    );
    expect(container.querySelector("[class*='rich-text-toolbar']")).toBeNull();
    const surface = screen.getByLabelText("Write a message");
    // Seleção explícita do trecho (Word): caret colapsado NÃO formata a mensagem inteira.
    const all = document.createRange();
    all.selectNodeContents(surface);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(all);
    fireEvent.click(screen.getByLabelText("Format"));
    expect(screen.getByRole("toolbar", { name: "Format" })).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Bold"));
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(screen.getByLabelText("Bold").getAttribute("aria-pressed")).toBe("true");
    // Re-seleciona o trecho: caret colapsado só sai do estilo de digitação (não unwrap).
    const again = document.createRange();
    again.selectNodeContents(surface);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(again);
    fireEvent.click(screen.getByLabelText("Bold"));
    expect(surface.innerHTML.toLowerCase()).not.toMatch(/<(strong|b)\b/);
    expect(screen.getByLabelText("Bold").getAttribute("aria-pressed")).toBe("false");

    fireEvent.click(screen.getByLabelText("Increase font size"));
    expect(surface.innerHTML).toMatch(/font-size:\s*18px/);

    fireEvent.paste(surface, {
      clipboardData: {
        getData: (type: string) =>
          type === "text/html" ? "<p>ok<script>alert(1)</script></p>" : "",
      },
    });
    expect(surface.innerHTML.toLowerCase()).not.toContain("<script");
    expect(surface.innerHTML.toLowerCase()).toContain("ok");
  });

  it("abre menu de emoji na faixa Formatar e insere o glifo", () => {
    document.execCommand = vi.fn().mockImplementation((cmd: string, _show?: boolean, value?: string) => {
      if (cmd === "insertHTML" && typeof value === "string") {
        const selection = window.getSelection();
        const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
        if (range) {
          range.deleteContents();
          range.insertNode(document.createTextNode(value));
          selection?.collapseToEnd();
        }
        return true;
      }
      return true;
    });
    const onChange = vi.fn();
    render(
      <MentionComposer
        value=""
        onChange={onChange}
        onSubmit={vi.fn()}
        labels={{
          ...labels,
          formatToggleAriaLabel: "Format",
          formatEmojiAriaLabel: "Emoji",
          emojiMenuAriaLabel: "Insert emoji",
        }}
        classNames={classNames}
      />,
    );
    fireEvent.click(screen.getByLabelText("Format"));
    fireEvent.click(screen.getByLabelText("Emoji"));
    expect(screen.getByRole("dialog", { name: "Insert emoji" })).toBeTruthy();
    fireEvent.mouseDown(screen.getByRole("option", { name: "Sorrindo" }));
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toContain("😀");
  });

  it("fonte com caret colapsado não seleciona a mensagem inteira", () => {
    const formatLabels = {
      ...labels,
      formatToggleAriaLabel: "Format",
      formatFontSizeAriaLabel: "Font size",
      formatFontSizeDecreaseAriaLabel: "Decrease font size",
      formatFontSizeIncreaseAriaLabel: "Increase font size",
    };
    render(
      <MentionComposer
        value="mensagem fonte"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        labels={formatLabels}
        classNames={classNames}
      />,
    );
    const surface = screen.getByLabelText("Write a message");
    const caret = document.createRange();
    caret.selectNodeContents(surface);
    caret.collapse(false);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(caret);

    fireEvent.click(screen.getByLabelText("Format"));
    fireEvent.click(screen.getByLabelText("Increase font size"));

    const selection = window.getSelection();
    expect(selection?.toString()).not.toBe("mensagem fonte");
    expect(selection?.getRangeAt(0)?.collapsed).toBe(true);
    expect(surface.innerHTML).toMatch(/font-size:\s*18px/);
    expect(readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "mentionComposerCaret.ts"),
      "utf8",
    )).not.toMatch(/expandCollapsedSelectionForFormat/);
  });

  it("expõe Desfazer/Refazer via pilha markdown sem RichTextEditor", () => {
    const source = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "MentionComposer.tsx"),
      "utf8",
    );
    expect(source).not.toMatch(/from ["'][^"']*RichTextToolbar["']/);
    expect(source).not.toMatch(/from ["'][^"']*RichTextEditor["']/);
    expect(source).not.toMatch(/<EditorHistoryActions/);
    expect(source).not.toMatch(/runRichTextCommand\(el, command\)/);
    expect(source).not.toMatch(/queryRichTextCommandEnabled/);
    expect(source).not.toMatch(/runRichTextCommand\([^)]*["']undo["']/);
    expect(source).toMatch(/createMentionComposerHistory/);
    expect(source).toMatch(/appendShortcutHint/);
    expect(source).toMatch(/runHistory\("undo"\)/);

    document.execCommand = vi.fn().mockReturnValue(true);

    const onChange = vi.fn();
    const formatLabels = {
      ...labels,
      formatToggleAriaLabel: "Format",
      formatBoldAriaLabel: "Bold",
      formatUndoAriaLabel: "Undo",
      formatRedoAriaLabel: "Redo",
    };
    render(
      <MentionComposer
        value="abc"
        onChange={onChange}
        onSubmit={vi.fn()}
        labels={formatLabels}
        classNames={classNames}
      />,
    );
    const surface = screen.getByLabelText("Write a message");
    const all = document.createRange();
    all.selectNodeContents(surface);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(all);

    fireEvent.click(screen.getByLabelText("Format"));
    const undoBtn = screen.getByLabelText("Undo") as HTMLButtonElement;
    expect(Boolean(undoBtn.disabled)).toEqual(true);
    fireEvent.click(screen.getByLabelText("Bold"));
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(Boolean((screen.getByLabelText("Undo") as HTMLButtonElement).disabled)).toEqual(
      false,
    );

    fireEvent.click(screen.getByLabelText("Undo"));
    expect(surface.innerHTML.toLowerCase()).not.toMatch(/<(strong|b)\b/);
    expect(surface.textContent?.replace(/\u200b/g, "")).toContain("abc");
    expect(document.execCommand).not.toHaveBeenCalledWith("undo", false, undefined);
  });

  it("Desfazer após negrito restaura texto pré-formato; Refazer reaplica", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    const formatLabels = {
      ...labels,
      formatToggleAriaLabel: "Format",
      formatBoldAriaLabel: "Bold",
      formatUndoAriaLabel: "Undo",
      formatRedoAriaLabel: "Redo",
    };
    render(
      <MentionComposer
        value="gravida enim."
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        labels={formatLabels}
        classNames={classNames}
      />,
    );
    const surface = screen.getByLabelText("Write a message");
    const all = document.createRange();
    all.selectNodeContents(surface);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(all);
    fireEvent.click(screen.getByLabelText("Format"));
    fireEvent.click(screen.getByLabelText("Bold"));
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);

    fireEvent.click(screen.getByLabelText("Undo"));
    const plain = surface.textContent?.replace(/\u200b/g, "") ?? "";
    expect(plain).toContain("gravida enim.");
    expect(surface.innerHTML.toLowerCase()).not.toMatch(/<(strong|b)\b/);

    fireEvent.click(screen.getByLabelText("Redo"));
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(document.execCommand).not.toHaveBeenCalledWith("undo", false, undefined);
    expect(document.execCommand).not.toHaveBeenCalledWith("redo", false, undefined);
  });

  it("Mod+Z desfaz formato sem chamar execCommand undo", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    const formatLabels = {
      ...labels,
      formatToggleAriaLabel: "Format",
      formatBoldAriaLabel: "Bold",
      formatUndoAriaLabel: "Undo",
      formatRedoAriaLabel: "Redo",
    };
    render(
      <MentionComposer
        value="xyz"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        labels={formatLabels}
        classNames={classNames}
      />,
    );
    const surface = screen.getByLabelText("Write a message");
    const all = document.createRange();
    all.selectNodeContents(surface);
    window.getSelection()?.removeAllRanges();
    window.getSelection()?.addRange(all);
    fireEvent.click(screen.getByLabelText("Format"));
    fireEvent.click(screen.getByLabelText("Bold"));
    expect(surface.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);

    fireEvent.keyDown(surface, { key: "z", ctrlKey: true });
    expect(surface.innerHTML.toLowerCase()).not.toMatch(/<(strong|b)\b/);
    expect(document.execCommand).not.toHaveBeenCalledWith("undo", false, undefined);
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
    const textareaFocus =
      css.match(
        /\.delpi-ui-mention-composer__textarea:focus-visible \{[^}]+\}/,
      )?.[0] ?? "";
    expect(textareaFocus).toMatch(/outline:\s*none/);
    expect(textareaFocus).toMatch(/box-shadow:\s*none/);
    expect(textareaFocus).toMatch(/border:\s*none/);
    expect(sendBlocks.join("\n")).toMatch(/width:\s*36px;/);
    expect(sendBlocks.join("\n")).toMatch(/border-radius:\s*50%;/);
    expect(css).toMatch(/max-height:\s*min\(40vh, 16rem\)/);
    expect(css).toMatch(/__format-bar/);
    expect(css).toMatch(/font-weight:\s*700/);
    expect(css).not.toMatch(/textarea::placeholder/);
    expect(css).not.toMatch(/--empty::before/);
    expect(css).toMatch(/__placeholder/);
    expect(css).toMatch(/__format\[aria-pressed="true"\]/);
    expect(css).not.toMatch(/\.delpi-ui-mention-composer__textarea pre \{/);
    const prose = readFileSync(join(stylesDir, "collaboration-rich-prose.css"), "utf8");
    expect(prose).toMatch(/\.delpi-ui-mention-composer__textarea code,/);
    expect(prose).toMatch(/\.delpi-ui-mention-composer__textarea pre,/);
    expect(prose).toMatch(/\.delpi-ui-mention-composer__textarea blockquote,/);
    expect(prose).toMatch(/code:empty/);
    expect(prose).toMatch(/blockquote::before/);
    expect(prose).toMatch(/border-left:\s*3px/);
    expect(prose).toMatch(/content:\s*"“"/);
    expect(prose).toMatch(/padding-left:\s*1\.25rem/);
    expect(css).toMatch(/__document-tray/);
    expect(css).toMatch(/__image-thumbs/);
    expect(css).toMatch(/position:\s*absolute/);
  });

  it("separa imagens na pílula e documentos na bandeja", () => {
    const onRemove = vi.fn();
    render(
      <MentionComposer
        classNames={classNames}
        labels={labels}
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
        pendingAttachments={[
          {
            id: "img-1",
            fileName: "foto.png",
            contentType: "image/png",
            previewUrl: "blob:test-img",
          },
          {
            id: "doc-1",
            fileName: "relatorio.pdf",
            contentType: "application/pdf",
            detail: "12 KB",
          },
        ]}
        onRemovePendingAttachment={onRemove}
      />,
    );
    expect(screen.getByTestId("mention-composer-image-thumbs")).toBeTruthy();
    expect(screen.getByTestId("mention-composer-document-tray")).toBeTruthy();
    expect(screen.getByText("relatorio.pdf")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Remove foto.png"));
    expect(onRemove).toHaveBeenCalledWith("img-1");
  });

  it("shows reply banner above the pill and cancels", () => {
    const onCancelReply = vi.fn();
    render(
      <MentionComposer
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
        labels={{
          ...labels,
          replyCancelAriaLabel: "Cancel reply",
        }}
        classNames={classNames}
        replyTo={{ label: "Replying to Ana", preview: "Hello there" }}
        onCancelReply={onCancelReply}
      />,
    );
    expect(screen.getByTestId("mention-composer-reply-banner")).toBeTruthy();
    expect(screen.getByText("Replying to Ana")).toBeTruthy();
    expect(screen.getByText("Hello there")).toBeTruthy();
    fireEvent.click(screen.getByLabelText("Cancel reply"));
    expect(onCancelReply).toHaveBeenCalledTimes(1);
  });

  it("emoji-insert-menu.css usa grade sem borda full de caixa", () => {
    const css = readFileSync(join(stylesDir, "emoji-insert-menu.css"), "utf8");
    expect(css).toMatch(/\.delpi-ui-emoji-insert-menu \{/);
    expect(css).toMatch(/grid-template-columns:\s*repeat\(8/);
    expect(css).toMatch(/__option/);
  });
});
