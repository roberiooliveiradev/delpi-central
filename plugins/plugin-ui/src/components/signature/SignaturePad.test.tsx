import { describe, expect, it } from "vitest";

import { SignaturePad } from "./SignaturePad";
import { RichTextEditor } from "../rich-text/RichTextEditor";
import { UserDirectoryPicker } from "../directory/UserDirectoryPicker";

describe("cipa shared exports", () => {
  it("exports SignaturePad", () => {
    expect(typeof SignaturePad).toBe("function");
  });

  it("exports RichTextEditor", () => {
    expect(typeof RichTextEditor).toBe("function");
  });

  it("exports UserDirectoryPicker", () => {
    expect(typeof UserDirectoryPicker).toBe("function");
  });
});
