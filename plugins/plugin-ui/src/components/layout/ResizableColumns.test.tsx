import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ResizableColumns,
  RESIZABLE_COLUMNS_KEYBOARD_STEP_PX,
  resizableColumnsBemClasses,
} from "./ResizableColumns";

const classNames = resizableColumnsBemClasses("test");
const labels = {
  separatorAriaLabel: "Resize inbox",
  collapseAriaLabel: "Collapse inbox",
  expandAriaLabel: "Expand inbox",
};

afterEach(() => {
  cleanup();
});

describe("ResizableColumns", () => {
  it("resizes with arrow keys and reports width", () => {
    const onLeftWidthChange = vi.fn();
    render(
      <ResizableColumns
        classNames={classNames}
        labels={labels}
        defaultLeftWidthPx={280}
        left={<div>Inbox</div>}
        right={<div>Thread</div>}
        onLeftWidthChange={onLeftWidthChange}
      />,
    );
    const separator = screen.getByRole("separator", { name: "Resize inbox" });
    fireEvent.keyDown(separator, { key: "ArrowRight" });
    expect(onLeftWidthChange).toHaveBeenCalledWith(
      280 + RESIZABLE_COLUMNS_KEYBOARD_STEP_PX,
    );
  });

  it("collapses to a rail and restores", () => {
    render(
      <ResizableColumns
        classNames={classNames}
        labels={labels}
        left={<div>Inbox</div>}
        right={<div>Thread</div>}
      />,
    );
    expect(screen.getByText("Inbox")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Collapse inbox" }));
    expect(screen.queryByText("Inbox")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Expand inbox" }));
    expect(screen.getByText("Inbox")).toBeTruthy();
  });
});
