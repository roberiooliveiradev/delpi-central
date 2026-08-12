import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SignaturePad, scaleSignatureStrokes } from "./SignaturePad";
import { RichTextEditor } from "../rich-text/RichTextEditor";
import { UserDirectoryPicker } from "../directory/UserDirectoryPicker";

describe("cipa shared exports", () => {
  it("exports SignaturePad", () => {
    expect(typeof SignaturePad).toBe("function");
  });

  it("exports RichTextEditor", () => {
    expect(typeof RichTextEditor).toBe("function");
  });

  it("exports UserDirectoryPicker", () => {
    expect(typeof UserDirectoryPicker).toBe("function");
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function mockCanvasContext() {
  const context = {
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    setTransform: vi.fn(),
    lineWidth: 2,
    lineCap: "round",
    lineJoin: "round",
    strokeStyle: "#0f172a",
  };
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
    context as unknown as CanvasRenderingContext2D,
  );
  vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function toBlob(
    this: HTMLCanvasElement,
    cb: BlobCallback,
  ) {
    cb(new Blob(["png"], { type: "image/png" }));
  });
  return context;
}

describe("SignaturePad", () => {
  it("mantém o bitmap transparente e aplica DPR no canvas", () => {
    const context = mockCanvasContext();
    Object.defineProperty(window, "devicePixelRatio", { configurable: true, value: 2 });

    const { container } = render(<SignaturePad width={640} height={220} />);
    const canvas = container.querySelector(".delpi-ui-signature-pad__canvas") as HTMLCanvasElement;
    const paper = container.querySelector(".delpi-ui-signature-pad__paper") as HTMLElement;

    expect(context.clearRect).toHaveBeenCalled();
    expect(context.setTransform).toHaveBeenCalledWith(2, 0, 0, 2, 0, 0);
    expect(canvas.width).toBeGreaterThan(0);
    expect(canvas.height).toBeGreaterThan(0);
    expect(paper.className).toContain("delpi-ui-signature-pad__paper");
  });

  it("marca html ao entrar em tela cheia para o host esconder o toggle de tema", () => {
    mockCanvasContext();
    render(<SignaturePad />);
    expect(document.documentElement.dataset.delpiSignatureFullscreen).toBeUndefined();
    fireEvent.click(screen.getByTestId("signature-pad-fullscreen"));
    expect(document.documentElement.dataset.delpiSignatureFullscreen).toBe("1");
    fireEvent.click(screen.getByTestId("signature-pad-fullscreen"));
    expect(document.documentElement.dataset.delpiSignatureFullscreen).toBeUndefined();
  });

  it("desfaz e refaz traços e limpa com onChange(null)", async () => {
    mockCanvasContext();
    const onChange = vi.fn();
    const { container } = render(<SignaturePad onChange={onChange} />);
    const canvas = container.querySelector(".delpi-ui-signature-pad__canvas") as HTMLCanvasElement;
    vi.spyOn(canvas, "getBoundingClientRect").mockReturnValue({
      left: 0,
      top: 0,
      width: 640,
      height: 220,
      right: 640,
      bottom: 220,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    fireEvent.pointerDown(canvas, { clientX: 10, clientY: 10, pointerId: 1 });
    fireEvent.pointerMove(canvas, { clientX: 40, clientY: 40, pointerId: 1 });
    fireEvent.pointerUp(canvas, { pointerId: 1 });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled();
    });
    expect((screen.getByTestId("signature-pad-undo") as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(screen.getByTestId("signature-pad-undo"));
    expect(onChange).toHaveBeenCalledWith(null);
    expect((screen.getByTestId("signature-pad-redo") as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(screen.getByTestId("signature-pad-redo"));
    expect(onChange.mock.calls.some((call) => call[0] instanceof Blob)).toBe(true);

    fireEvent.click(screen.getByTestId("signature-pad-clear"));
    expect(onChange).toHaveBeenLastCalledWith(null);
  });

  it("preserva traços ao entrar em tela cheia", async () => {
    const context = mockCanvasContext();
    const { container } = render(<SignaturePad width={640} height={220} />);
    const canvas = container.querySelector(".delpi-ui-signature-pad__canvas") as HTMLCanvasElement;
    const paper = container.querySelector(".delpi-ui-signature-pad__paper") as HTMLElement;
    Object.defineProperty(paper, "clientWidth", { configurable: true, get: () => 640 });
    vi.spyOn(canvas, "getBoundingClientRect").mockReturnValue({
      left: 0,
      top: 0,
      width: 640,
      height: 220,
      right: 640,
      bottom: 220,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });

    fireEvent.pointerDown(canvas, { clientX: 10, clientY: 10, pointerId: 1 });
    fireEvent.pointerMove(canvas, { clientX: 80, clientY: 60, pointerId: 1 });
    fireEvent.pointerUp(canvas, { pointerId: 1 });

    expect((screen.getByTestId("signature-pad-undo") as HTMLButtonElement).disabled).toBe(false);
    const strokesAfterDraw = context.stroke.mock.calls.length;

    Object.defineProperty(paper, "clientWidth", { configurable: true, get: () => 960 });
    fireEvent.click(screen.getByTestId("signature-pad-fullscreen"));

    await waitFor(() => {
      expect(context.stroke.mock.calls.length).toBeGreaterThan(strokesAfterDraw);
    });
    expect((screen.getByTestId("signature-pad-undo") as HTMLButtonElement).disabled).toBe(false);
    expect(container.querySelector(".delpi-ui-signature-pad--fullscreen")).toBeTruthy();
  });

  it("entra e sai de tela cheia sem crash (HelpTooltip + createPortal)", () => {
    mockCanvasContext();
    const { container } = render(<SignaturePad />);
    const toggle = screen.getByTestId("signature-pad-fullscreen");

    fireEvent.click(toggle);
    expect(container.querySelector(".delpi-ui-signature-pad--fullscreen")).toBeTruthy();
    expect(document.documentElement.dataset.delpiSignatureFullscreen).toBe("1");

    // Simula hover no help (balão usa createPortal) e saída da tela cheia.
    const helps = container.querySelectorAll(".delpi-ui-help-tooltip__trigger, button[aria-label^='Ajuda']");
    if (helps.length > 0) {
      fireEvent.mouseEnter(helps[0]!);
      fireEvent.focus(helps[0]!);
    }

    fireEvent.click(toggle);
    expect(container.querySelector(".delpi-ui-signature-pad--fullscreen")).toBeFalsy();
    expect(document.documentElement.dataset.delpiSignatureFullscreen).toBeUndefined();
    expect(screen.getByTestId("signature-pad-fullscreen")).toBeTruthy();
  });

  it("scaleSignatureStrokes mantém proporção", () => {
    const scaled = scaleSignatureStrokes(
      [[{ x: 10, y: 20, lineWidth: 2 }]],
      { width: 100, height: 50 },
      { width: 200, height: 100 },
    );
    expect(scaled[0][0]).toEqual({ x: 20, y: 40, lineWidth: 4 });
  });
});
