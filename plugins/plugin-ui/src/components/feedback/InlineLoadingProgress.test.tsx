import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  clampInlineLoadingPercent,
  InlineLoadingProgress,
  inlineLoadingProgressBemClasses,
} from "./InlineLoadingProgress";

describe("InlineLoadingProgress", () => {
  it("clampInlineLoadingPercent limita 0–100", () => {
    expect(clampInlineLoadingPercent(-5)).toBe(0);
    expect(clampInlineLoadingPercent(42.4)).toBe(42);
    expect(clampInlineLoadingPercent(42.6)).toBe(43);
    expect(clampInlineLoadingPercent(150)).toBe(100);
  });

  it("expõe progressbar com percentual real", () => {
    render(<InlineLoadingProgress percent={67} label="Carregando dados" />);
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuenow")).toBe("67");
    expect(bar.getAttribute("aria-label")).toBe("Carregando dados: 67%");
    expect(screen.getByText("67%")).toBeTruthy();
    expect(screen.getByText("Carregando dados")).toBeTruthy();
  });

  it("aplica dual-class com prefixo do plugin", () => {
    const cn = inlineLoadingProgressBemClasses("td");
    const { container } = render(
      <InlineLoadingProgress percent={10} classNames={cn} showLabel={false} />,
    );
    const root = container.firstElementChild as HTMLElement;
    expect(root.className).toContain("td-inline-loading-progress");
    expect(root.className).toContain("delpi-ui-inline-loading-progress");
    expect(root.className).toContain("delpi-ui-inline-loading-progress--compact");
  });
});
