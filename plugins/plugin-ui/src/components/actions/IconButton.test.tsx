import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { IconButton } from "./IconButton";

afterEach(() => {
  cleanup();
});

describe("IconButton", () => {
  it("dispara onClick e aplica dual-class canônica", () => {
    const onClick = vi.fn();
    const { container } = render(
      <IconButton aria-label="Remover" onClick={onClick}>
        ×
      </IconButton>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Remover" }));
    expect(onClick).toHaveBeenCalledTimes(1);
    expect(container.querySelector(".delpi-ui-icon-btn")).toBeTruthy();
  });

  it("aplica tone danger", () => {
    const { container } = render(
      <IconButton aria-label="Excluir" tone="danger">
        ×
      </IconButton>,
    );
    expect(container.querySelector(".delpi-ui-icon-btn--danger")).toBeTruthy();
  });
});
