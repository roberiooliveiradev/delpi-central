import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AttachmentPreviewStrip,
  attachmentPreviewStripBemClasses,
} from "./AttachmentPreviewStrip";

afterEach(() => {
  cleanup();
});

const labels = {
  empty: "Sem anexos",
  openAriaLabel: (fileName: string) => `Abrir ${fileName}`,
  removeAriaLabel: (fileName: string) => `Remover ${fileName}`,
};

describe("AttachmentPreviewStrip", () => {
  it("mostra vazio e itens clicáveis em modo preview", () => {
    const { rerender } = render(
      <AttachmentPreviewStrip
        items={[]}
        onOpen={vi.fn()}
        classNames={attachmentPreviewStripBemClasses("cm")}
        labels={labels}
      />,
    );
    expect(screen.getByText("Sem anexos")).toBeTruthy();

    const onOpen = vi.fn();
    rerender(
      <AttachmentPreviewStrip
        heading="Anexos (1)"
        items={[{ id: "1", fileName: "foto.png", detail: "10 KB" }]}
        onOpen={onOpen}
        classNames={attachmentPreviewStripBemClasses("cm")}
        labels={labels}
      />,
    );
    expect(screen.getByText("Anexos (1)")).toBeTruthy();
    expect(screen.getByText("foto.png")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Remover foto\.png/ })).toBeNull();
    screen.getByRole("button", { name: /Abrir foto\.png/ }).click();
    expect(onOpen).toHaveBeenCalledWith(
      expect.objectContaining({ id: "1", fileName: "foto.png" }),
    );
  });

  it("modo manage exibe remover sem disparar onOpen", () => {
    const onOpen = vi.fn();
    const onRemove = vi.fn();
    render(
      <AttachmentPreviewStrip
        mode="manage"
        items={[{ id: "1", fileName: "foto.png" }]}
        onOpen={onOpen}
        onRemove={onRemove}
        classNames={attachmentPreviewStripBemClasses("cm")}
        labels={labels}
      />,
    );
    const remove = screen.getByRole("button", { name: /Remover foto\.png/ });
    remove.click();
    expect(onRemove).toHaveBeenCalledWith(
      expect.objectContaining({ id: "1", fileName: "foto.png" }),
    );
    expect(onOpen).not.toHaveBeenCalled();
  });
});
