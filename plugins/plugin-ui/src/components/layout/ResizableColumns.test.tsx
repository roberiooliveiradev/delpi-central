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
    const expand = screen.getByRole("button", { name: "Expand inbox" });
    expect(expand.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(expand);
    expect(screen.getByText("Inbox")).toBeTruthy();
  });

  it("collapse button stops propagation so handle drag does not start", () => {
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
    const collapse = screen.getByRole("button", { name: "Collapse inbox" });
    fireEvent.pointerDown(collapse, { button: 0, pointerId: 1 });
    fireEvent.pointerMove(separator, { clientX: 400, pointerId: 1 });
    expect(onLeftWidthChange).not.toHaveBeenCalled();
    fireEvent.click(collapse);
    expect(screen.queryByText("Inbox")).toBeNull();
  });
});
