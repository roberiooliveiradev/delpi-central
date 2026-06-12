import { describe, expect, it } from "vitest";

import { workspaceFileIngestFamilyForContentVariant } from "./useWorkspaceFileIngestPolicy";

describe("useWorkspaceFileIngestPolicy helpers", () => {
  it("mapeia variantes de dropzone para famílias da API", () => {
    expect(workspaceFileIngestFamilyForContentVariant("session")).toBe("session_attachment");
    expect(workspaceFileIngestFamilyForContentVariant("agent")).toBe("agent_source");
    expect(workspaceFileIngestFamilyForContentVariant("project")).toBe("project_source");
    expect(workspaceFileIngestFamilyForContentVariant("workspace")).toBe("global_knowledge");
    expect(workspaceFileIngestFamilyForContentVariant("context")).toBe("context_paste");
  });
});
