import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  AttachmentFileList,
  attachmentFileListBemClasses,
} from "./AttachmentFileList";

afterEach(() => {
  cleanup();
});

describe("AttachmentFileList", () => {
  it("mostra vazio e itens com ações", () => {
    const labels = {
      open: "Abrir",
      download: "Baixar",
      remove: "Remover",
      empty: "Sem anexos",
    };
    const { rerender } = render(
      <AttachmentFileList
        items={[]}
        classNames={attachmentFileListBemClasses("cm")}
        labels={labels}
      />,
    );
    expect(screen.getByText("Sem anexos")).toBeTruthy();

    const onOpen = vi.fn();
    const onDownload = vi.fn();
    const onRemove = vi.fn();
    rerender(
      <AttachmentFileList
        items={[{ id: "1", fileName: "nota.pdf", detail: "10 KB" }]}
        classNames={attachmentFileListBemClasses("cm")}
        labels={labels}
        onOpen={onOpen}
        onDownload={onDownload}
        onRemove={onRemove}
      />,
    );
    expect(screen.getByText("nota.pdf")).toBeTruthy();
    expect(screen.getByText("10 KB")).toBeTruthy();
    screen.getByRole("button", { name: "Abrir" }).click();
    screen.getByRole("button", { name: "Baixar" }).click();
    screen.getByRole("button", { name: "Remover" }).click();
    expect(onOpen).toHaveBeenCalled();
    expect(onDownload).toHaveBeenCalled();
    expect(onRemove).toHaveBeenCalled();
  });
});
