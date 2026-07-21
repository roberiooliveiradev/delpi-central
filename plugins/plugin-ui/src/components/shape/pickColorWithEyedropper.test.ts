import { describe, expect, it, vi, afterEach } from "vitest";

import { isEyedropperSupported, pickColorWithEyedropper } from "./pickColorWithEyedropper";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("pickColorWithEyedropper", () => {
  it("retorna null sem EyeDropper", async () => {
    vi.stubGlobal("EyeDropper", undefined);
    expect(isEyedropperSupported()).toBe(false);
    expect(await pickColorWithEyedropper()).toBeNull();
  });

  it("retorna hex do EyeDropper", async () => {
    class FakeEyeDropper {
      open() {
        return Promise.resolve({ sRGBHex: "#112233" });
      }
    }
    vi.stubGlobal("EyeDropper", FakeEyeDropper);
    expect(isEyedropperSupported()).toBe(true);
    expect(await pickColorWithEyedropper()).toBe("#112233");
  });

  it("retorna null se o usuário cancelar", async () => {
    class FakeEyeDropper {
      open() {
        return Promise.reject(new DOMException("Aborted", "AbortError"));
      }
    }
    vi.stubGlobal("EyeDropper", FakeEyeDropper);
    expect(await pickColorWithEyedropper()).toBeNull();
  });
});
