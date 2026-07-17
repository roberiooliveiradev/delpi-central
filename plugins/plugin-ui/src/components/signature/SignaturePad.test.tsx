import { cleanup, render } from "@testing-library/react";
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

describe("SignaturePad", () => {
  it("mantém o bitmap transparente e usa CSS para o fundo visual", () => {
    const context = {
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
    };
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(
      context as unknown as CanvasRenderingContext2D,
    );

    const { container } = render(<SignaturePad />);

    expect(context.clearRect).toHaveBeenCalledWith(0, 0, 640, 220);
    expect(container.querySelector(".delpi-ui-signature-pad__canvas")).toBeTruthy();
  });
});
