import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ConversationFileDropLayer,
  conversationFileDropLayerBemClasses,
} from "./ConversationFileDropLayer";

const classNames = conversationFileDropLayerBemClasses("test");

afterEach(() => {
  cleanup();
});

describe("ConversationFileDropLayer", () => {
  it("shows overlay on dragover and drops accepted files", () => {
    const onFiles = vi.fn();
    const { container } = render(
      <ConversationFileDropLayer
        classNames={classNames}
        overlayLabel="Drop files"
        accept=".pdf,application/pdf"
        maxBytes={1024}
        onFiles={onFiles}
      >
        <div>Thread</div>
      </ConversationFileDropLayer>,
    );
    const root = container.firstChild as HTMLElement;
    fireEvent.dragOver(root, { dataTransfer: { files: [] } });
    expect(screen.getByRole("status").textContent).toBe("Drop files");
    const pdf = new File(["x"], "a.pdf", { type: "application/pdf" });
    const huge = new File(["too-big-file-content-here"], "big.pdf", {
      type: "application/pdf",
    });
    fireEvent.drop(root, { dataTransfer: { files: [pdf, huge] } });
    expect(onFiles).toHaveBeenCalledTimes(1);
    expect(onFiles.mock.calls[0]?.[0]?.map((file: File) => file.name)).toEqual(["a.pdf"]);
    expect(screen.queryByRole("status")).toBeNull();
  });
});
