import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  __resetScopedPrintForTests,
  printScopedWindow,
  scheduleTargetWindowPrint,
} from "./printOnce";

describe("printScopedWindow", () => {
  beforeEach(() => {
    __resetScopedPrintForTests();
    vi.useFakeTimers();
  });

  afterEach(() => {
    __resetScopedPrintForTests();
    vi.useRealTimers();
    vi.restoreAllMocks();
    document.body.className = "";
    document.documentElement.className = "";
  });

  it("bloqueia segundo print enquanto a sessão estiver ativa", () => {
    const print = vi.spyOn(window, "print").mockImplementation(() => {});

    expect(printScopedWindow({ bodyClassName: "delpi-ui-document-printing", deferFrames: false })).toBe(
      true,
    );
    expect(printScopedWindow({ bodyClassName: "delpi-ui-document-printing", deferFrames: false })).toBe(
      false,
    );
    expect(print).toHaveBeenCalledTimes(1);
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(true);

    window.dispatchEvent(new Event("afterprint"));
    expect(document.body.classList.contains("delpi-ui-document-printing")).toBe(false);

    expect(printScopedWindow({ deferFrames: false })).toBe(true);
    expect(print).toHaveBeenCalledTimes(2);
  });
});

describe("scheduleTargetWindowPrint", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("não chama print duas vezes quando imagens prontas e fallback competem", () => {
    const print = vi.fn();
    const img = document.createElement("img");
    Object.defineProperty(img, "complete", { value: true });

    const fakeWindow = {
      closed: false,
      focus: vi.fn(),
      scrollTo: vi.fn(),
      print,
      document: { images: [img] },
      addEventListener: vi.fn(),
    } as unknown as Window;

    scheduleTargetWindowPrint(fakeWindow);
    vi.advanceTimersByTime(1_000);
    vi.advanceTimersByTime(150);
    expect(print).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(2_000);
    expect(print).toHaveBeenCalledTimes(1);
  });
});
