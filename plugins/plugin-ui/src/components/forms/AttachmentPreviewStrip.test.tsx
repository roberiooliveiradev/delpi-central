import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AttachmentPreviewStrip,
  attachmentPreviewStripBemClasses,
} from "./AttachmentPreviewStrip";

afterEach(() => {
  cleanup();
});

describe("AttachmentPreviewStrip", () => {
  it("mostra vazio e itens clicáveis", () => {
    const labels = {
      empty: "Sem anexos",
      openAriaLabel: (fileName: string) => `Abrir ${fileName}`,
    };
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
    screen.getByRole("button", { name: /foto\.png/ }).click();
    expect(onOpen).toHaveBeenCalledWith(
      expect.objectContaining({ id: "1", fileName: "foto.png" }),
    );
  });
});
