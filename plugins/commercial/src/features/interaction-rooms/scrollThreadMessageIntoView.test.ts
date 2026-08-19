import { describe, expect, it, vi } from "vitest";

import {
  pinTitleFromMessageBody,
  scrollThreadMessageIntoView,
} from "./scrollThreadMessageIntoView";

describe("scrollThreadMessageIntoView", () => {
  it("encontra o item, faz scroll e marca highlight", () => {
    vi.useFakeTimers();
    const item = {
      classList: {
        add: vi.fn(),
        remove: vi.fn(),
      },
      scrollIntoView: vi.fn(),
    };
    const root = {
      querySelector: vi.fn(() => item),
    } as unknown as ParentNode;

    const found = scrollThreadMessageIntoView(root, "msg-1");
    expect(found).toBe(item);
    expect(item.scrollIntoView).toHaveBeenCalledWith({ block: "center" });
    expect(item.classList.add).toHaveBeenCalledWith("is-pin-target");
    vi.advanceTimersByTime(1500);
    expect(item.classList.remove).toHaveBeenCalledWith("is-pin-target");
    vi.useRealTimers();
  });

  it("retorna null sem id ou sem elemento", () => {
    expect(scrollThreadMessageIntoView(null, "x")).toBeNull();
    const root = { querySelector: () => null } as unknown as ParentNode;
    expect(scrollThreadMessageIntoView(root, "")).toBeNull();
    expect(scrollThreadMessageIntoView(root, "missing")).toBeNull();
  });

  it("resume o corpo da mensagem para o pin", () => {
    expect(pinTitleFromMessageBody("  olá  mundo  ", "x")).toBe("olá mundo");
    expect(pinTitleFromMessageBody("", "fallback")).toBe("fallback");
    expect(pinTitleFromMessageBody("a".repeat(90), "x").endsWith("…")).toBe(true);
  });
});
