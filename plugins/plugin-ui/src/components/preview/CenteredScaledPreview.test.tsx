import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CenteredScaledPreview } from "./CenteredScaledPreview";

describe("CenteredScaledPreview", () => {
  it("aplica escala uniforme a partir do menor fator width/height", () => {
    const observe = vi.fn();
    const disconnect = vi.fn();
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn(() => ({
        observe,
        disconnect,
        unobserve: vi.fn(),
      })),
    );

    Object.defineProperty(HTMLElement.prototype, "clientWidth", {
      configurable: true,
      get() {
        return 160;
      },
    });
    Object.defineProperty(HTMLElement.prototype, "clientHeight", {
      configurable: true,
      get() {
        return 90;
      },
    });

    const { container } = render(
      <CenteredScaledPreview referenceWidth={320} referenceHeight={180}>
        <div data-testid="inner">Slide</div>
      </CenteredScaledPreview>,
    );

    const content = container.querySelector(".delpi-ui-centered-scaled-preview__content") as HTMLElement;
    expect(content.style.width).toBe("320px");
    expect(content.style.height).toBe("180px");
    expect(content.style.transform).toBe("scale(0.5)");
    expect(content.style.left).toBe("50%");
    expect(content.style.top).toBe("50%");
    expect(content.style.marginLeft).toBe("-160px");
    expect(content.style.marginTop).toBe("-90px");
    expect(content.style.visibility).toBe("visible");
  });

  it("não usa scale(1) antes de medir o container", () => {
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn(() => ({
        observe: vi.fn(),
        disconnect: vi.fn(),
        unobserve: vi.fn(),
      })),
    );

    Object.defineProperty(HTMLElement.prototype, "clientWidth", {
      configurable: true,
      get() {
        return 0;
      },
    });
    Object.defineProperty(HTMLElement.prototype, "clientHeight", {
      configurable: true,
      get() {
        return 0;
      },
    });

    const { container } = render(
      <CenteredScaledPreview referenceWidth={1920} referenceHeight={1080}>
        <div>Slide</div>
      </CenteredScaledPreview>,
    );

    const content = container.querySelector(".delpi-ui-centered-scaled-preview__content") as HTMLElement;
    expect(content.style.transform).toBe("scale(0)");
    expect(content.style.visibility).toBe("hidden");
  });
});
