import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RichTextEditor } from "./RichTextEditor";
import { RICH_TEXT_LABELS } from "./richTextLabels";

function toolbarButton(name: string) {
  const toolbar = screen.getByRole("toolbar", { name: RICH_TEXT_LABELS.toolbar });
  return within(toolbar).getAllByRole("button", { name })[0]!;
}

afterEach(() => {
  cleanup();
});

describe("RichTextEditor", () => {
  it("renderiza toolbar moderna com tipografia, parágrafo e inserção", () => {
    render(<RichTextEditor value="<p>Teste</p>" onChange={() => undefined} />);
    expect(screen.getByRole("toolbar", { name: RICH_TEXT_LABELS.toolbar })).toBeTruthy();
    expect(screen.getByRole("group", { name: RICH_TEXT_LABELS.fontSize })).toBeTruthy();
    const fontFamily = screen.getByRole("button", { name: RICH_TEXT_LABELS.fontFamily });
    expect(fontFamily.closest(".delpi-ui-help-tooltip--wrap")).toBeTruthy();
    const fontSizeDown = screen.getByRole("button", { name: RICH_TEXT_LABELS.fontSizeDecrease });
    const fontSizeUp = screen.getByRole("button", { name: RICH_TEXT_LABELS.fontSizeIncrease });
    expect(fontSizeDown.closest(".delpi-ui-help-tooltip--wrap")).toBeTruthy();
    expect(fontSizeUp.closest(".delpi-ui-help-tooltip--wrap")).toBeTruthy();
    expect(screen.getByRole("button", { name: RICH_TEXT_LABELS.textColor }).closest(".delpi-ui-help-tooltip--wrap")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: RICH_TEXT_LABELS.highlightColor }).closest(".delpi-ui-help-tooltip--wrap"),
    ).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.table)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.horizontalRule)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.bold)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.sourceHtml)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.sourceMarkdown)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.sourceVisual)).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Editor de texto" })).toBeTruthy();
  });

  it("renderiza preview sem toolbar e preserva tabela", () => {
    const { container } = render(
      <RichTextEditor
        value='<table class="delpi-ui-rich-text-table"><tr><th>A</th></tr></table>'
        onChange={() => undefined}
        mode="preview"
      />,
    );
    expect(container.querySelector(".delpi-ui-rich-text-ribbon")).toBeNull();
    expect(container.querySelector("table.delpi-ui-rich-text-table")).toBeTruthy();
  });

  it("alterna para fonte HTML e desabilita formatação", () => {
    const { container } = render(
      <RichTextEditor value="<p>Olá</p>" onChange={() => undefined} />,
    );

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceHtml));

    expect(screen.getByRole("textbox", { name: RICH_TEXT_LABELS.sourceEditor })).toBeTruthy();
    expect((toolbarButton(RICH_TEXT_LABELS.bold) as HTMLButtonElement).disabled).toBe(true);
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    expect(editor.getAttribute("contenteditable")).toBe("false");
    expect(editor.getAttribute("aria-hidden")).toBe("true");
  });

  it("volta ao visual a partir da fonte HTML", () => {
    const onChange = vi.fn();
    const { container } = render(<RichTextEditor value="<p>Olá</p>" onChange={onChange} />);

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceHtml));
    const source = screen.getByRole("textbox", { name: RICH_TEXT_LABELS.sourceEditor });
    fireEvent.change(source, {
      target: { value: '<p style="font-size:18px">Editado</p>' },
    });
    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceVisual));

    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    expect(editor.getAttribute("contenteditable")).toBe("true");
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toContain("Editado");
    expect(last.toLowerCase()).not.toContain("<script");
  });

  it("alterna Visual ↔ Markdown e sincroniza HTML", () => {
    const onChange = vi.fn();
    render(<RichTextEditor value="<p><strong>Olá</strong></p>" onChange={onChange} />);

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceMarkdown));
    const source = screen.getByRole("textbox", {
      name: RICH_TEXT_LABELS.sourceMarkdownEditor,
    });
    expect((source as HTMLTextAreaElement).value).toMatch(/\*\*Olá\*\*/);

    fireEvent.change(source, { target: { value: "## Título\n\n- item" } });
    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceVisual));

    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toContain("<h2>");
    expect(last).toContain("<ul>");
    expect(last.toLowerCase()).not.toContain("<script");
  });

  it("cola Markdown plain como HTML sanitizado", () => {
    const onChange = vi.fn();
    const { container } = render(
      <RichTextEditor value="<p></p>" onChange={onChange} />,
    );
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    expect(editor).toBeTruthy();

    const clipboardData = {
      getData: (type: string) => {
        if (type === "text/html") return "";
        if (type === "text/plain") return "# Título\n\n**negrito**\n\n- um";
        return "";
      },
    };

    fireEvent.paste(editor, { clipboardData });
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toMatch(/<h1>|<h2>/);
    expect(last.toLowerCase()).not.toContain("<script");
  });

  it("mantém o contentEditable montado ao alternar fonte (preserva formatação)", () => {
    const { container } = render(
      <RichTextEditor value="<p>Olá</p>" onChange={() => undefined} />,
    );
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    expect(editor).toBeTruthy();
    expect(editor.style.display).not.toBe("none");

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceHtml));
    const sameEditor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    expect(sameEditor).toBe(editor);
    expect(sameEditor.style.display).toBe("none");
    expect(sameEditor.getAttribute("contenteditable")).toBe("false");

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceVisual));
    expect(editor.style.display).not.toBe("none");
    expect(editor.getAttribute("contenteditable")).toBe("true");
  });

  it("positive: onPasteImages materializa File e insert no caret", async () => {
    const onChange = vi.fn();
    const onPasteImages = vi.fn(async (files: File[]) =>
      files.map((file) => ({
        src: "blob:http://localhost/preview",
        pendingId: "pend-1",
        alt: file.name,
      })),
    );
    const { container } = render(
      <RichTextEditor value="<p></p>" onChange={onChange} onPasteImages={onPasteImages} />,
    );
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    const file = new File([new Uint8Array([1, 2, 3])], "shot.png", { type: "image/png" });
    const clipboardData = {
      files: {
        length: 1,
        0: file,
        item: (i: number) => (i === 0 ? file : null),
        [Symbol.iterator]: function* () {
          yield file;
        },
      },
      items: [{ kind: "file", type: "image/png", getAsFile: () => file }],
      types: ["Files", "image/png"],
      getData: () => "",
    };
    fireEvent.paste(editor, { clipboardData });
    await vi.waitFor(() => expect(onPasteImages).toHaveBeenCalled());
    expect(onPasteImages.mock.calls[0]?.[0]?.[0]?.name).toBe("shot.png");
    await vi.waitFor(() => expect(onChange).toHaveBeenCalled());
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toMatch(/data-attachment-pending=["']pend-1["']/);
  });

  it("irmão: paste Markdown sem onPasteImages continua convertendo texto", () => {
    const onChange = vi.fn();
    const { container } = render(
      <RichTextEditor value="<p></p>" onChange={onChange} />,
    );
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    fireEvent.paste(editor, {
      clipboardData: {
        getData: (type: string) =>
          type === "text/plain" ? "# Título\n\n**negrito**" : "",
        files: { length: 0, item: () => null, [Symbol.iterator]: function* () {} },
        items: [],
        types: ["text/plain"],
      },
    });
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toMatch(/<h1>|<h2>/);
  });

  it("negativo: sem onPasteImages, imagem no clipboard não chama host", () => {
    const onChange = vi.fn();
    const { container } = render(
      <RichTextEditor value="<p></p>" onChange={onChange} />,
    );
    const editor = container.querySelector(".delpi-ui-rich-text__editor") as HTMLElement;
    const file = new File([new Uint8Array([1])], "x.png", { type: "image/png" });
    fireEvent.paste(editor, {
      clipboardData: {
        files: {
          length: 1,
          0: file,
          item: (i: number) => (i === 0 ? file : null),
          [Symbol.iterator]: function* () {
            yield file;
          },
        },
        items: [{ kind: "file", type: "image/png", getAsFile: () => file }],
        types: ["Files"],
        getData: () => "",
      },
    });
    // Sem handler, paste de imagem não é o contrato H12 — não inventa insert.
    expect(editor.querySelector("img")).toBeNull();
  });
});
