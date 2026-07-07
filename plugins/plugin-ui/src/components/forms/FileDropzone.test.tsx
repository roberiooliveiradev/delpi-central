import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { FileDropzone, fileDropzoneKaizenClasses } from "./FileDropzone";

afterEach(() => {
  cleanup();
});

describe("FileDropzone", () => {
  it("renderiza título e hint", () => {
    render(
      <FileDropzone
        onFilesSelected={vi.fn()}
        classNames={fileDropzoneKaizenClasses()}
        labels={{
          title: "Arraste arquivos",
          hint: "PDF ou imagem",
        }}
      />,
    );

    expect(screen.getByText("Arraste arquivos")).toBeTruthy();
    expect(screen.getByText("PDF ou imagem")).toBeTruthy();
  });
});
