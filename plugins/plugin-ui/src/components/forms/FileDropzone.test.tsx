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

  it("renderiza emptyContent customizado", () => {
    render(
      <FileDropzone
        onFilesSelected={vi.fn()}
        classNames={fileDropzoneKaizenClasses()}
        labels={{ title: "Padrão", hint: "Ignorado" }}
        emptyContent={<span>Layout customizado</span>}
      />,
    );

    expect(screen.getByText("Layout customizado")).toBeTruthy();
    expect(screen.queryByText("Padrão")).toBeNull();
  });
});
