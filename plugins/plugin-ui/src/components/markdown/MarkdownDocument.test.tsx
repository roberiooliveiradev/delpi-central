import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { buildMarkdownDocumentModel } from "./markdownDocumentModel";
import { MarkdownDocumentView } from "./MarkdownDocument";

describe("MarkdownDocumentView — internal anchors", () => {
  it("delega clique em link interno ao callback e preserva o hash externo", () => {
    window.location.hash = "#documentacao/doc-1";
    const model = buildMarkdownDocumentModel(
      "## Conclusão\n\n[Voltar à conclusão](#conclusao)",
    );
    const onInternalAnchorNavigate = vi.fn();
    const { container } = render(
      <MarkdownDocumentView
        model={model}
        onInternalAnchorNavigate={onInternalAnchorNavigate}
      />,
    );
    const anchor = container.querySelector('a[href="#conclusao"]');
    expect(anchor).not.toBeNull();
    fireEvent.click(anchor as Element);
    expect(onInternalAnchorNavigate).toHaveBeenCalledWith("conclusao");
    expect(window.location.hash).toBe("#documentacao/doc-1");
  });

  it("sem callback, não intercepta o comportamento padrão do link", () => {
    const model = buildMarkdownDocumentModel("[Ver](#secao)");
    const { container } = render(<MarkdownDocumentView model={model} />);
    const anchor = container.querySelector('a[href="#secao"]');
    expect(anchor).not.toBeNull();
    const event = new MouseEvent("click", { bubbles: true, cancelable: true });
    anchor?.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
  });

  it("links externos permanecem navegação normal (não delega)", () => {
    const model = buildMarkdownDocumentModel("[Site](https://example.com)");
    const onInternalAnchorNavigate = vi.fn();
    const { container } = render(
      <MarkdownDocumentView
        model={model}
        onInternalAnchorNavigate={onInternalAnchorNavigate}
      />,
    );
    const anchor = container.querySelector("a[href='https://example.com']");
    expect(anchor).not.toBeNull();
    fireEvent.click(anchor as Element);
    expect(onInternalAnchorNavigate).not.toHaveBeenCalled();
  });
});
