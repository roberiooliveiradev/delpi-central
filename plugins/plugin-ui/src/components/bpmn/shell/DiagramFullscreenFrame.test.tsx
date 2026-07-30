import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DiagramFullscreenFrame } from "./DiagramFullscreenFrame";

afterEach(cleanup);

describe("DiagramFullscreenFrame", () => {
  it("mostra botão Tela cheia e abre ModalShell com o conteúdo", () => {
    render(
      <div className="dashboard-transformometro">
        <DiagramFullscreenFrame title="Diagrama de teste" subtitle="Subtítulo">
          <p>Conteúdo do editor</p>
        </DiagramFullscreenFrame>
      </div>,
    );

    expect(screen.getByRole("button", { name: /Tela cheia/i })).toBeTruthy();
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Tela cheia/i }));

    const dialog = screen.getByRole("dialog", { name: "Diagrama de teste" });
    expect(dialog).toBeTruthy();
    expect(dialog.className).toContain("delpi-ui-modal");
    expect(dialog.className).toContain("delpi-ui-modal--host-fill");
    expect(screen.getByText("Conteúdo do editor")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Sair da tela cheia/i })).toBeTruthy();
  });

  it("fecha com Sair da tela cheia", () => {
    render(
      <div className="dashboard-transformometro">
        <DiagramFullscreenFrame title="Diagrama">
          <p>Editor</p>
        </DiagramFullscreenFrame>
      </div>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Tela cheia/i }));
    fireEvent.click(screen.getByRole("button", { name: /Sair da tela cheia/i }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("button", { name: /Tela cheia/i })).toBeTruthy();
  });

  it("enabled=false omite o botão", () => {
    render(
      <DiagramFullscreenFrame title="Diagrama" enabled={false}>
        <p>Só inline</p>
      </DiagramFullscreenFrame>,
    );
    expect(screen.queryByRole("button", { name: /Tela cheia/i })).toBeNull();
    expect(screen.getByText("Só inline")).toBeTruthy();
  });
});
