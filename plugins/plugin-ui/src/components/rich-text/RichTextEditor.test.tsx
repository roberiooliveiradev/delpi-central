import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RichTextEditor } from "./RichTextEditor";
import { RICH_TEXT_LABELS } from "./richTextLabels";

describe("RichTextEditor", () => {
  it("renderiza toolbar moderna com tipografia, parágrafo e inserção", () => {
    render(<RichTextEditor value="<p>Teste</p>" onChange={() => undefined} />);
    expect(screen.getByRole("toolbar", { name: RICH_TEXT_LABELS.toolbar })).toBeTruthy();
    expect(screen.getByRole("group", { name: RICH_TEXT_LABELS.fontSize })).toBeTruthy();
    expect(screen.getByRole("button", { name: RICH_TEXT_LABELS.table })).toBeTruthy();
    expect(screen.getByRole("button", { name: RICH_TEXT_LABELS.bold })).toBeTruthy();
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
});
