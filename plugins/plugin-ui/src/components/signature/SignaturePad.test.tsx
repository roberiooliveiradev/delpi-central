import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SignaturePad } from "./SignaturePad";
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

    expect(context.clearRect).toHaveBeenCalled();
    expect(context.setTransform).toHaveBeenCalledWith(2, 0, 0, 2, 0, 0);
    expect(canvas.width).toBe(1280);
    expect(canvas.height).toBe(440);
  });

  it("desfaz e refaz traços e limpa com onChange(null)", () => {
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

    expect(onChange).toHaveBeenCalled();
    expect((screen.getByTestId("signature-pad-undo") as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(screen.getByTestId("signature-pad-undo"));
    expect(onChange).toHaveBeenCalledWith(null);
    expect((screen.getByTestId("signature-pad-redo") as HTMLButtonElement).disabled).toBe(false);

    fireEvent.click(screen.getByTestId("signature-pad-redo"));
    expect(onChange.mock.calls.some((call) => call[0] instanceof Blob)).toBe(true);

    fireEvent.click(screen.getByTestId("signature-pad-clear"));
    expect(onChange).toHaveBeenLastCalledWith(null);
  });

  it("altera espessura via presets", () => {
    mockCanvasContext();
    const onStrokeWidthChange = vi.fn();
    render(<SignaturePad onStrokeWidthChange={onStrokeWidthChange} />);
    fireEvent.click(screen.getByTestId("signature-pad-stroke-thick"));
    expect(onStrokeWidthChange).toHaveBeenCalledWith("thick");
  });
});
