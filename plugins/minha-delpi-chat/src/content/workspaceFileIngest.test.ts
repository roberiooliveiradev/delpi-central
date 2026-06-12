import { describe, expect, it } from "vitest";

import attachmentsContent from "./attachments_content.json";
import {
  workspaceFileMessageEditAttachmentsHeader,
  workspaceFileReadingStatusLabel,
} from "./workspaceFileIngestContent";

describe("workspaceFileIngest regression (Playbook 17)", () => {
  it("F6 — labels de status vêm do JSON espelhado", () => {
    const jsonLabels = attachmentsContent.preview.readingStatus;

    expect(workspaceFileReadingStatusLabel("indexed")).toBe(jsonLabels.indexed);
    expect(workspaceFileReadingStatusLabel("indexing")).toBe(jsonLabels.indexing);
    expect(workspaceFileReadingStatusLabel("index_failed")).toBe(jsonLabels.index_failed);
  });

  it("F7 — cabeçalho de edição de mensagem usa messageEdit do JSON", () => {
    expect(workspaceFileMessageEditAttachmentsHeader(2)).toBe(
      attachmentsContent.ingestUi.messageEdit.attachmentsHeader.replace("{count}", "2"),
    );
    expect(attachmentsContent.ingestUi.messageEdit.addMoreLabel).toBe("Anexar mais");
  });
});
