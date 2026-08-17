import { afterEach, describe, expect, it, vi } from "vitest";

import {
  flushRegisteredEditorAutosave,
  registerPreviewHandoff,
} from "./previewHandoff";

describe("previewHandoff", () => {
  afterEach(() => {
    registerPreviewHandoff(null);
  });

  it("flushRegisteredEditorAutosave chama o flush registrado", async () => {
    const flush = vi.fn(async () => undefined);
    registerPreviewHandoff({ flush });
    await flushRegisteredEditorAutosave();
    expect(flush).toHaveBeenCalledTimes(1);
  });

  it("flushRegisteredEditorAutosave é no-op sem handoff", async () => {
    await expect(flushRegisteredEditorAutosave()).resolves.toBeUndefined();
  });
});
