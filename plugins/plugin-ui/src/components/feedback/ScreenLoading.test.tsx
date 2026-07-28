import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import {
  ScreenLoading,
  createDashboardScreenLoading,
  screenLoadingBemClasses,
} from "./ScreenLoading";

describe("ScreenLoading", () => {
  it("renderiza label e classes canônicas fullscreen/dark", () => {
    const { container } = render(
      <ScreenLoading label="Carregando apresentação" variant="fullscreen" tone="dark" />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("delpi-ui-screen-loading");
    expect(root.className).toContain("delpi-ui-screen-loading--fullscreen");
    expect(root.className).toContain("delpi-ui-screen-loading--dark");
    expect(root.getAttribute("role")).toBe("status");
    expect(root.getAttribute("aria-busy")).toBe("true");
    expect(screen.getByText("Carregando apresentação")).toBeTruthy();
  });

  it("factory aplica prefixo BEM dual-class", () => {
    const cn = screenLoadingBemClasses("pub");
    const DashboardScreenLoading = createDashboardScreenLoading({
      classNames: cn,
      defaultLabel: "Aguarde",
      variant: "embedded",
      tone: "brand",
    });
    const { container } = render(<DashboardScreenLoading />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("pub-screen-loading");
    expect(root.className).toContain("delpi-ui-screen-loading");
    expect(root.className).toContain("delpi-ui-screen-loading--brand");
    expect(screen.getByText("Aguarde")).toBeTruthy();
  });
});
