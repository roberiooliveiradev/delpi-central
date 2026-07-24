import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { printDelpiDocumentHtml } from "./delpiDocumentPrint";

describe("printDelpiDocumentHtml", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("não reabre o diálogo quando o fallback de imagens dispara após o primeiro print", () => {
    const print = vi.fn();
    const img = document.createElement("img");
    Object.defineProperty(img, "complete", { value: true });

    const fakeDoc = {
      open: vi.fn(),
      write: vi.fn(),
      close: vi.fn(),
      images: [img] as unknown as HTMLCollectionOf<HTMLImageElement>,
    };

    const fakeWindow = {
      closed: false,
      focus: vi.fn(),
      scrollTo: vi.fn(),
      print,
      document: fakeDoc,
      addEventListener: vi.fn(),
    } as unknown as Window;

    vi.spyOn(window, "open").mockReturnValue(fakeWindow);

    expect(printDelpiDocumentHtml("<html></html>")).toBe(true);

    vi.advanceTimersByTime(1_000);
    vi.advanceTimersByTime(150);
    expect(print).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(2_000);
    expect(print).toHaveBeenCalledTimes(1);
  });
});
