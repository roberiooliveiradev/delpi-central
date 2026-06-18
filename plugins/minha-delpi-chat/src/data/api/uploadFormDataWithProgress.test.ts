import { describe, expect, it, vi } from "vitest";

import {
  composeBatchUploadProgress,
  uploadFormDataWithProgress,
} from "./uploadFormDataWithProgress";

describe("uploadFormDataWithProgress", () => {
  it("calcula progresso agregado em lote", () => {
    expect(composeBatchUploadProgress(0, 2, 50)).toBe(25);
    expect(composeBatchUploadProgress(1, 2, 100)).toBe(100);
  });

  it("reporta progresso durante upload XHR", async () => {
    const progress: number[] = [];

    class MockXHR {
      upload = {
        onprogress: null as ((event: ProgressEvent) => void) | null,
        onload: null as (() => void) | null,
      };

      onload: (() => void) | null = null;

      onerror: (() => void) | null = null;

      onabort: (() => void) | null = null;

      responseText = '{"ok":true}';

      status = 200;

      statusText = "OK";

      open = vi.fn();

      setRequestHeader = vi.fn();

      send = vi.fn(() => {
        this.upload.onprogress?.({
          lengthComputable: true,
          loaded: 50,
          total: 100,
        } as ProgressEvent);
        this.upload.onload?.();
        this.onload?.();
      });
    }

    vi.stubGlobal("XMLHttpRequest", MockXHR as unknown as typeof XMLHttpRequest);

    const result = await uploadFormDataWithProgress("/upload", new FormData(), {
      onUploadProgress: (value) => progress.push(value),
      parseResponse: async (response) => {
        expect(response.status).toBe(200);
        return { ok: true };
      },
    });

    expect(result).toEqual({ ok: true });
    expect(progress[0]).toBe(0);
    expect(progress).toContain(44);
    expect(progress).toContain(90);
    expect(progress.at(-1)).toBe(100);

    vi.unstubAllGlobals();
  });
});
