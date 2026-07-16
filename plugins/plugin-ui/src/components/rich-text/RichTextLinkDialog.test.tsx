// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RichTextLinkDialog } from "./RichTextLinkDialog";

afterEach(cleanup);

describe("RichTextLinkDialog", () => {
  it("usa ModalShell do kit (sem prompt do navegador)", () => {
    render(
      <RichTextLinkDialog open initialUrl="" onSubmit={() => {}} onClose={() => {}} />,
    );

    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("delpi-ui-modal");
    expect(screen.getByText("Inserir link")).toBeTruthy();
  });

  it("aplica a URL digitada e desabilita Aplicar sem URL", () => {
    const onSubmit = vi.fn();
    render(<RichTextLinkDialog open onSubmit={onSubmit} onClose={() => {}} />);

    const apply = screen.getByRole("button", { name: "Aplicar" }) as HTMLButtonElement;
    expect(apply.disabled).toBe(true);

    fireEvent.change(screen.getByPlaceholderText("https://…"), {
      target: { value: "https://delpi.com.br" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar" }));

    expect(onSubmit).toHaveBeenCalledWith("https://delpi.com.br");
  });

  it("pré-preenche a URL no modo edição", () => {
    render(
      <RichTextLinkDialog
        open
        editing
        initialUrl="https://x.dev"
        onSubmit={() => {}}
        onClose={() => {}}
      />,
    );

    expect(screen.getByText("Editar link")).toBeTruthy();
    expect((screen.getByPlaceholderText("https://…") as HTMLInputElement).value).toBe(
      "https://x.dev",
    );
  });
});
