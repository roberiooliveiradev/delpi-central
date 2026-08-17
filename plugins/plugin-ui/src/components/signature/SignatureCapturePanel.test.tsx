import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { SignatureCapturePanel } from "./SignatureCapturePanel";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("SignatureCapturePanel", () => {
  it("gera blob ao digitar o nome", async () => {
    const onChange = vi.fn();
    HTMLCanvasElement.prototype.toBlob = function toBlob(cb: BlobCallback) {
      cb(new Blob(["typed"], { type: "image/png" }));
    };
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      fillText: vi.fn(),
      fillStyle: "",
      textAlign: "center",
      textBaseline: "middle",
      font: "",
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

    render(<SignatureCapturePanel modes={["type"]} onChange={onChange} showPreview />);
    fireEvent.change(screen.getByTestId("signature-capture-type-input"), {
      target: { value: "Maria Silva" },
    });
    fireEvent.click(screen.getByTestId("signature-capture-type-apply"));

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled();
      expect(onChange.mock.calls[0][0]).toBeInstanceOf(Blob);
    });
  });

  it("aceita upload PNG", async () => {
    const onChange = vi.fn();
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => ({
        width: 100,
        height: 40,
        close: vi.fn(),
      })),
    );
    HTMLCanvasElement.prototype.toBlob = function toBlob(cb: BlobCallback) {
      cb(new Blob(["upload"], { type: "image/png" }));
    };
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      drawImage: vi.fn(),
      getImageData: vi.fn(() => ({
        data: new Uint8ClampedArray(16),
        width: 2,
        height: 2,
      })),
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

    render(<SignatureCapturePanel modes={["upload"]} onChange={onChange} showPreview={false} />);
    const file = new File([new Uint8Array([1, 2, 3])], "sign.png", { type: "image/png" });
    fireEvent.change(screen.getByTestId("signature-capture-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled();
      expect(onChange.mock.calls[0][0]).toBeInstanceOf(Blob);
    });
  });

  it("aceita upload com MIME vazio e extensão .png", async () => {
    const onChange = vi.fn();
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => ({
        width: 100,
        height: 40,
        close: vi.fn(),
      })),
    );
    HTMLCanvasElement.prototype.toBlob = function toBlob(cb: BlobCallback) {
      cb(new Blob(["upload-empty-mime"], { type: "image/png" }));
    };
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      setTransform: vi.fn(),
      clearRect: vi.fn(),
      drawImage: vi.fn(),
      getImageData: vi.fn(() => ({
        data: new Uint8ClampedArray(16),
        width: 2,
        height: 2,
      })),
    })) as unknown as typeof HTMLCanvasElement.prototype.getContext;

    render(<SignatureCapturePanel modes={["upload"]} onChange={onChange} showPreview={false} />);
    const file = new File([new Uint8Array([1, 2, 3])], "assinatura.png", { type: "" });
    fireEvent.change(screen.getByTestId("signature-capture-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(onChange).toHaveBeenCalled();
    });
  });

  it("mostra erro e não limpa assinatura anterior em arquivo inválido", async () => {
    const onChange = vi.fn();
    render(<SignatureCapturePanel modes={["upload"]} onChange={onChange} showPreview={false} />);
    const file = new File(["not-image"], "nota.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByTestId("signature-capture-upload-input"), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.getByTestId("signature-capture-upload-error")).toBeTruthy();
    });
    expect(onChange).not.toHaveBeenCalled();
  });
});
