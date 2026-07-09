import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { StatusBadge, statusBadgeBemClasses } from "./StatusBadge";

afterEach(() => {
  cleanup();
});

describe("StatusBadge", () => {
  it("renderiza variant danger", () => {
    const { container } = render(
      <StatusBadge
        label="média 5.7"
        variant="danger"
        classNames={statusBadgeBemClasses("si")}
      />,
    );

    expect(screen.getByText("média 5.7")).toBeTruthy();
    expect(container.querySelector(".si-status-badge--danger")).toBeTruthy();
  });
});
