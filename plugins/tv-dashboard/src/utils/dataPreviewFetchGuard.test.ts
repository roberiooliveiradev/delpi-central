import { describe, expect, it, vi } from "vitest";

import {
  createLinkedTimeoutSignal,
  DATA_PREVIEW_TIMEOUT_MESSAGE,
  formatDataPreviewLoadingLabel,
  isAbortError,
  resolveDataSourceProgressLabel,
  resolvePreviewAbortMessage,
} from "./dataPreviewFetchGuard";

describe("dataPreviewFetchGuard", () => {
  it("formata rótulo com fonte única e contagem multi", () => {
    expect(
      formatDataPreviewLoadingLabel({
        completed: 0,
        total: 1,
        pendingLabels: ["get_kaizen_summary"],
      }),
    ).toBe("Carregando get_kaizen_summary");
    expect(
      formatDataPreviewLoadingLabel({
        completed: 1,
        total: 3,
        pendingLabels: ["get_ppm_external", "get_5s"],
      }),
    ).toBe("Carregando 1/3: get_ppm_external");
  });

  it("resolve rótulo da fonte por title ou operationId", () => {
    expect(
      resolveDataSourceProgressLabel({
        id: "src-1",
        title: "Kaizen",
        dataBinding: { operationId: "get_kaizen" },
      }),
    ).toBe("Kaizen");
    expect(
      resolveDataSourceProgressLabel({
        id: "src-1",
        dataBinding: { operationId: "get_kaizen" },
      }),
    ).toBe("get_kaizen");
  });

  it("resolvePreviewAbortMessage distingue timeout, cancelamento e erro", () => {
    expect(resolvePreviewAbortMessage(new Error("boom"), false)).toBe("boom");
    expect(resolvePreviewAbortMessage(new DOMException("x", "AbortError"), true)).toBeNull();
    expect(
      resolvePreviewAbortMessage(
        new DOMException(DATA_PREVIEW_TIMEOUT_MESSAGE, "TimeoutError"),
        false,
      ),
    ).toBe(DATA_PREVIEW_TIMEOUT_MESSAGE);
    expect(isAbortError(new DOMException("Aborted", "AbortError"))).toBe(true);
  });

  it("createLinkedTimeoutSignal aborta após o timeout", async () => {
    vi.useFakeTimers();
    const { signal, cleanup } = createLinkedTimeoutSignal(1000);
    expect(signal.aborted).toBe(false);
    vi.advanceTimersByTime(1000);
    expect(signal.aborted).toBe(true);
    cleanup();
    vi.useRealTimers();
  });
});
