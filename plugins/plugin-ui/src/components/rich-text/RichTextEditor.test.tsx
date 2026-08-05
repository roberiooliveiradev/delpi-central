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
    expect(toolbarButton(RICH_TEXT_LABELS.table)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.bold)).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.sourceHtml)).toBeTruthy();
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
    render(<RichTextEditor value="<p>Olá</p>" onChange={() => undefined} />);

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceHtml));

    expect(screen.getByRole("textbox", { name: RICH_TEXT_LABELS.sourceEditor })).toBeTruthy();
    expect(toolbarButton(RICH_TEXT_LABELS.sourceVisual)).toBeTruthy();
    expect((toolbarButton(RICH_TEXT_LABELS.bold) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.queryByRole("textbox", { name: "Editor de texto" })).toBeNull();
  });

  it("volta ao visual a partir da fonte HTML", () => {
    const onChange = vi.fn();
    render(<RichTextEditor value="<p>Olá</p>" onChange={onChange} />);

    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceHtml));
    const source = screen.getByRole("textbox", { name: RICH_TEXT_LABELS.sourceEditor });
    fireEvent.change(source, {
      target: { value: '<p style="font-size:18px">Editado</p>' },
    });
    fireEvent.click(toolbarButton(RICH_TEXT_LABELS.sourceVisual));

    expect(screen.getByRole("textbox", { name: "Editor de texto" })).toBeTruthy();
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls.at(-1)?.[0] as string;
    expect(last).toContain("Editado");
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
});
