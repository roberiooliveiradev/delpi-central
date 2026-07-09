import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NativeTextAreaControl } from "./NativeTextAreaControl";

afterEach(() => {
  cleanup();
});

describe("NativeTextAreaControl", () => {
  it("propaga valor e onChange", () => {
    const handleChange = vi.fn();

    render(
      <NativeTextAreaControl
        value="inicial"
        aria-label="Código"
        onChange={handleChange}
      />,
    );

    fireEvent.change(screen.getByLabelText("Código"), { target: { value: "flowchart" } });
    expect(handleChange).toHaveBeenCalledWith("flowchart");
  });

  it("repassa onKeyDown", () => {
    const handleKeyDown = vi.fn();

    render(
      <NativeTextAreaControl
        value=""
        aria-label="Composer"
        onChange={() => undefined}
        onKeyDown={handleKeyDown}
      />,
    );

    fireEvent.keyDown(screen.getByLabelText("Composer"), { key: "Enter" });
    expect(handleKeyDown).toHaveBeenCalledTimes(1);
  });
});
