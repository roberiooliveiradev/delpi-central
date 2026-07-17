import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { StateBanner, stateBannerKaizenClasses } from "./StateBanner";

afterEach(() => {
  cleanup();
});

describe("StateBanner", () => {
  it("renderiza variante padrão", () => {
    const { container } = render(
      <StateBanner classNames={stateBannerKaizenClasses("kz")}>Carregando…</StateBanner>,
    );

    expect(screen.getByText("Carregando…")).toBeTruthy();
    expect(container.firstElementChild?.className).toContain("kz-state");
    expect(container.firstElementChild?.className).toContain("delpi-ui-state-banner");
  });

  it("aplica modificador de erro", () => {
    const { container } = render(
      <StateBanner variant="error" classNames={stateBannerKaizenClasses("kz")}>
        Falhou
      </StateBanner>,
    );

    expect(container.firstElementChild?.className).toContain("kz-state--error");
  });
});
