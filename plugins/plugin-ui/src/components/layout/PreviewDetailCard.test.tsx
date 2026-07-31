import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  PreviewDetailCard,
  previewDetailCardBemClasses,
} from "./PreviewDetailCard";

describe("PreviewDetailCard", () => {
  afterEach(() => {
    cleanup();
  });

  const classNames = previewDetailCardBemClasses("demo");

  it("emite dual-class canônico e slots media/detail", () => {
    render(
      <PreviewDetailCard
        classNames={classNames}
        media={<span>capa</span>}
        title="Programação"
        meta={<span>Ativa</span>}
        aria-label="Abrir Programação"
        onClick={() => undefined}
      />,
    );
    const root = screen.getByRole("button", { name: "Abrir Programação" });
    expect(root.className).toContain("demo-preview-detail-card");
    expect(root.className).toContain("delpi-ui-preview-detail-card");
    expect(root.querySelector(".delpi-ui-preview-detail-card__media")).toBeTruthy();
    expect(root.querySelector(".delpi-ui-preview-detail-card__detail")).toBeTruthy();
    expect(root.querySelector(".delpi-ui-preview-detail-card__meta")?.textContent).toBe(
      "Ativa",
    );
  });

  it("dispara onClick", () => {
    const onClick = vi.fn();
    render(
      <PreviewDetailCard
        classNames={classNames}
        media={null}
        title="X"
        aria-label="Abrir X"
        onClick={onClick}
      />,
    );
    screen.getByRole("button", { name: "Abrir X" }).click();
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});
