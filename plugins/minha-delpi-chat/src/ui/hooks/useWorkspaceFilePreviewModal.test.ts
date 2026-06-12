import { describe, expect, it } from "vitest";

import type { ChatWorkspaceSource } from "../../data/api/chatTypes";
import {
  buildWorkspaceLocalFilePreviewTarget,
  buildWorkspaceSourcePreviewTarget,
} from "./useWorkspaceFilePreviewModal";

describe("useWorkspaceFilePreviewModal helpers", () => {
  it("builds source preview target from workspace source", () => {
    const source = {
      id: "src-1",
      title: "Nota do projeto",
      original_filename: "90264234.pdf",
      content_type: "application/pdf",
    } as ChatWorkspaceSource;

    expect(buildWorkspaceSourcePreviewTarget(source)).toEqual({
      filename: "90264234.pdf",
      contentType: "application/pdf",
      serverSourceId: "src-1",
    });
  });

  it("falls back to source title when original filename is missing", () => {
    const source = {
      id: "src-2",
      title: "Regras internas",
      original_filename: null,
      content_type: "text/plain",
    } as ChatWorkspaceSource;

    expect(buildWorkspaceSourcePreviewTarget(source).filename).toBe("Regras internas");
  });

  it("builds local file preview target", () => {
    const file = new File(["conteudo"], "manual.txt", { type: "text/plain" });

    expect(buildWorkspaceLocalFilePreviewTarget(file)).toEqual({
      filename: "manual.txt",
      contentType: "text/plain",
      sizeBytes: file.size,
      localFile: file,
    });
  });
});
