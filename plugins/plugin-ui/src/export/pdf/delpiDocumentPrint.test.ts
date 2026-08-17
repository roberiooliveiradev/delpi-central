import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { printDelpiDocumentHtml } from "./delpiDocumentPrint";

function attachFakeIframeContent(iframe: HTMLIFrameElement): {
  print: ReturnType<typeof vi.fn>;
  write: ReturnType<typeof vi.fn>;
  fakeWindow: Window;
} {
  const print = vi.fn();
  const write = vi.fn();
  const fakeDoc = {
    open: vi.fn(),
    write,
    close: vi.fn(),
    images: [] as unknown as HTMLCollectionOf<HTMLImageElement>,
  };
  const listeners = new Map<string, Set<EventListener>>();
  const fakeWindow = {
    closed: false,
    focus: vi.fn(),
    scrollTo: vi.fn(),
    print,
    document: fakeDoc,
    addEventListener: vi.fn((type: string, listener: EventListener) => {
      const set = listeners.get(type) ?? new Set();
      set.add(listener);
      listeners.set(type, set);
    }),
    removeEventListener: vi.fn((type: string, listener: EventListener) => {
      listeners.get(type)?.delete(listener);
    }),
    dispatchEvent: (event: Event) => {
      listeners.get(event.type)?.forEach((listener) => listener(event));
      return true;
    },
  } as unknown as Window;

  Object.defineProperty(iframe, "contentWindow", { configurable: true, value: fakeWindow });
  Object.defineProperty(iframe, "contentDocument", { configurable: true, value: fakeDoc });
  return { print, write, fakeWindow };
}

describe("printDelpiDocumentHtml", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.innerHTML = "";
  });

  it("usa iframe oculto (sem window.open) e não cobre a UI com overlay", () => {
    const open = vi.spyOn(window, "open");
    const created: HTMLIFrameElement[] = [];
    const originalCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
      const el = originalCreate(tagName);
      if (tagName.toLowerCase() === "iframe") {
        created.push(el as HTMLIFrameElement);
        attachFakeIframeContent(el as HTMLIFrameElement);
      }
      return el;
    });

    expect(printDelpiDocumentHtml("<html><body>Ata</body></html>")).toBe(true);
    expect(open).not.toHaveBeenCalled();

    const iframe = created[0];
    expect(iframe).toBeTruthy();
    expect(iframe?.getAttribute("data-delpi-document-print-frame")).toBe("1");
    expect(iframe?.style.pointerEvents).toBe("none");
    expect(iframe?.style.zIndex).toBe("-1");
    expect(iframe?.style.width).toBe("210mm");
    expect(iframe?.style.height).toBe("297mm");
    expect(document.querySelectorAll("iframe[data-delpi-document-print-frame]").length).toBe(1);
  });

  it("não reabre o diálogo quando o fallback de imagens dispara após o primeiro print", () => {
    const created: HTMLIFrameElement[] = [];
    const originalCreate = document.createElement.bind(document);
    let print!: ReturnType<typeof vi.fn>;
    let fakeWindow!: Window;

    vi.spyOn(document, "createElement").mockImplementation((tagName: string) => {
      const el = originalCreate(tagName);
      if (tagName.toLowerCase() === "iframe") {
        created.push(el as HTMLIFrameElement);
        const attached = attachFakeIframeContent(el as HTMLIFrameElement);
        print = attached.print;
        fakeWindow = attached.fakeWindow;
        const img = document.createElement("img");
        Object.defineProperty(img, "complete", { value: true });
        (fakeWindow.document as { images: HTMLImageElement[] }).images = [img];
      }
      return el;
    });

    expect(printDelpiDocumentHtml("<html></html>")).toBe(true);

    vi.advanceTimersByTime(1_000);
    vi.advanceTimersByTime(150);
    expect(print).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(2_000);
    expect(print).toHaveBeenCalledTimes(1);

    expect(document.querySelector("iframe[data-delpi-document-print-frame]")).toBeTruthy();
    fakeWindow.dispatchEvent(new Event("afterprint"));
    expect(document.querySelector("iframe[data-delpi-document-print-frame]")).toBeNull();
  });
});
