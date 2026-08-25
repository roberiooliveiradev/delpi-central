import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PresentationStageControls } from "./PresentationStageControls";

afterEach(() => {
  cleanup();
});

describe("PresentationStageControls", () => {
  it("abre menu customizado de seções e salta ao clicar", () => {
    const onJump = vi.fn();
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        sections={[
          { id: "main", name: "Principal", sortOrder: 0, isMain: true },
          { id: "sec-b", name: "Produção", sortOrder: 1 },
        ]}
        onJumpToSection={onJump}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Ir para seção" }));
    expect(screen.getByRole("listbox", { name: "Seções" })).toBeTruthy();
    fireEvent.click(screen.getByRole("option", { name: "Produção" }));
    expect(onJump).toHaveBeenCalledWith("sec-b");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("não mostra salto quando só existe a seção principal", () => {
    render(
      <PresentationStageControls
        index={0}
        total={1}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        sections={[{ id: "main", name: "Principal", sortOrder: 0, isMain: true }]}
        onJumpToSection={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Ir para seção" })).toBeNull();
  });

  it("em reunião oculta Pausar e permite trocar modo", () => {
    const onMode = vi.fn();
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        playbackMode="meeting"
        onPlaybackModeChange={onMode}
      />,
    );
    expect(screen.queryByRole("button", { name: "Pausar" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Modo de reprodução" }));
    fireEvent.click(screen.getByRole("option", { name: /Apresentação/ }));
    expect(onMode).toHaveBeenCalledWith("presentation");
  });

  it("em apresentação mostra Pausar", () => {
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        playbackMode="presentation"
        onPlaybackModeChange={() => undefined}
      />,
    );
    expect(screen.getByRole("button", { name: "Pausar" })).toBeTruthy();
  });

  it("em reunião mostra Caneta/Laser/Limpar e alterna tool", () => {
    const onTool = vi.fn();
    const onClear = vi.fn();
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        playbackMode="meeting"
        annotationTool="none"
        onAnnotationToolChange={onTool}
        onClearAnnotations={onClear}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Caneta" }));
    expect(onTool).toHaveBeenCalledWith("pen");
    fireEvent.click(screen.getByRole("button", { name: "Limpar" }));
    expect(onClear).toHaveBeenCalled();
  });

  it("em apresentação não mostra ferramentas de anotação", () => {
    render(
      <PresentationStageControls
        index={0}
        total={2}
        paused={false}
        onPauseToggle={() => undefined}
        onPrevious={() => undefined}
        onNext={() => undefined}
        playbackMode="presentation"
        onAnnotationToolChange={() => undefined}
        onClearAnnotations={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Caneta" })).toBeNull();
  });
});
