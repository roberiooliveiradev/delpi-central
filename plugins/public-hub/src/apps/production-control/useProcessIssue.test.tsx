/** @vitest-environment jsdom */
import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ApiError, type PublicProcessIssueConfirmation } from "./api.ts";
import {
  useProcessIssue,
  type ProcessIssueSubmitResult,
} from "./useProcessIssue.ts";
import type { ProcessIssueDraft } from "./processIssue.ts";

type SubmitApi = NonNullable<
  Parameters<typeof useProcessIssue>[0]["submitApi"]
>;

const DRAFT: ProcessIssueDraft = {
  issueCode: "tool_not_linked",
  toolCode: "F12345",
  materialCode: null,
  note: null,
};

function setup(overrides: Partial<Parameters<typeof useProcessIssue>[0]> = {}) {
  const submitApi = vi.fn<SubmitApi>(async () => ({
    requestId: "req-9",
    requestNumber: "REQ-2026-000123",
    status: "submitted",
    message: "ok",
  }));
  let counter = 0;
  const generateKey = () => `key-${++counter}`;
  const onAuthError = vi.fn();
  const options = {
    token: "tok",
    productionOrder: "24640401002",
    operationCode: "03",
    sessionToken: "sess-1",
    onAuthError,
    submitApi,
    generateKey,
    ...overrides,
  };
  const hook = renderHook(() => useProcessIssue(options));
  return { hook, submitApi, generateKey, onAuthError };
}

const keysSent = (submitApi: { mock: { calls: unknown[][] } }) =>
  submitApi.mock.calls.map((call) => call[2]);

describe("useProcessIssue", () => {
  it("submits successfully and stores the confirmation", async () => {
    const { hook, submitApi } = setup();
    act(() => hook.result.current.beginAttempt());
    let result: ProcessIssueSubmitResult | undefined;
    await act(async () => {
      result = await hook.result.current.submit(DRAFT);
    });
    expect(result?.ok).toBe(true);
    expect(submitApi).toHaveBeenCalledTimes(1);
    expect(submitApi.mock.calls[0][3]).toMatchObject({
      productionOrder: "24640401002",
      operationCode: "03",
      issueCode: "tool_not_linked",
      toolCode: "F12345",
    });
    expect(hook.result.current.confirmation?.requestNumber).toBe(
      "REQ-2026-000123",
    );
  });

  it("does nothing without session", async () => {
    const { hook, submitApi } = setup({ sessionToken: null });
    act(() => hook.result.current.beginAttempt());
    let result: ProcessIssueSubmitResult | undefined;
    await act(async () => {
      result = await hook.result.current.submit(DRAFT);
    });
    expect(result?.ok).toBe(false);
    expect(submitApi).not.toHaveBeenCalled();
  });

  it("toggles busy while submitting", async () => {
    let resolve: (v: PublicProcessIssueConfirmation) => void = () => undefined;
    const submitApi = vi.fn<SubmitApi>(
      () =>
        new Promise<PublicProcessIssueConfirmation>((res) => {
          resolve = res;
        }),
    );
    const { hook } = setup({ submitApi });
    act(() => hook.result.current.beginAttempt());
    let promise: Promise<unknown> = Promise.resolve();
    act(() => {
      promise = hook.result.current.submit(DRAFT);
    });
    expect(hook.result.current.submitting).toBe(true);
    await act(async () => {
      resolve({ requestId: "r", requestNumber: "N", status: "submitted", message: null });
      await promise;
    });
    expect(hook.result.current.submitting).toBe(false);
  });

  it("blocks concurrent submits (double click)", async () => {
    let resolve: (v: PublicProcessIssueConfirmation) => void = () => undefined;
    const submitApi = vi.fn<SubmitApi>(
      () =>
        new Promise<PublicProcessIssueConfirmation>((res) => {
          resolve = res;
        }),
    );
    const { hook } = setup({ submitApi });
    act(() => hook.result.current.beginAttempt());
    let first: Promise<unknown> = Promise.resolve();
    let second: Promise<unknown> = Promise.resolve();
    act(() => {
      first = hook.result.current.submit(DRAFT);
      second = hook.result.current.submit(DRAFT);
    });
    await act(async () => {
      resolve({ requestId: "r", requestNumber: "N", status: "ok", message: null });
      await Promise.all([first, second]);
    });
    expect(submitApi).toHaveBeenCalledTimes(1);
  });

  it("401 invalidates the session and returns the friendly message", async () => {
    const submitApi = vi.fn<SubmitApi>(async () => {
      throw new ApiError("Sessão inválida.", 401);
    });
    const onAuthError = vi.fn();
    const { hook } = setup({ submitApi, onAuthError });
    act(() => hook.result.current.beginAttempt());
    let result: ProcessIssueSubmitResult | undefined;
    await act(async () => {
      result = await hook.result.current.submit(DRAFT);
    });
    expect(onAuthError).toHaveBeenCalledTimes(1);
    expect(result?.ok).toBe(false);
    expect(result?.message).toBe(
      "Identifique-se novamente para enviar a solicitação.",
    );
  });

  it("503 returns the retry message without clearing the attempt", async () => {
    const submitApi = vi
      .fn<SubmitApi>()
      .mockRejectedValueOnce(new ApiError("down", 503))
      .mockResolvedValueOnce({
        requestId: "r",
        requestNumber: "REQ-1",
        status: "submitted",
        message: null,
      });
    const { hook } = setup({ submitApi });
    act(() => hook.result.current.beginAttempt());

    let failed: ProcessIssueSubmitResult | undefined;
    await act(async () => {
      failed = await hook.result.current.submit(DRAFT);
    });
    expect(failed?.ok).toBe(false);
    expect(failed?.message).toContain("Tente novamente");

    // retry com o MESMO payload reutiliza a mesma Idempotency-Key
    let retried: ProcessIssueSubmitResult | undefined;
    await act(async () => {
      retried = await hook.result.current.submit(DRAFT);
    });
    expect(retried?.ok).toBe(true);
    expect(keysSent(submitApi)[0]).toBe(keysSent(submitApi)[1]);
  });

  it("changed payload after an error generates a new key", async () => {
    const submitApi = vi
      .fn<SubmitApi>()
      .mockRejectedValueOnce(new ApiError("down", 503))
      .mockResolvedValue({
        requestId: "r",
        requestNumber: "REQ-1",
        status: "submitted",
        message: null,
      });
    const { hook } = setup({ submitApi });
    act(() => hook.result.current.beginAttempt());
    await act(async () => {
      await hook.result.current.submit(DRAFT);
    });
    await act(async () => {
      await hook.result.current.submit({ ...DRAFT, note: "mudou" });
    });
    const keys = keysSent(submitApi);
    expect(keys[0]).not.toBe(keys[1]);
  });

  it("success ends the attempt — a new opening uses a new key", async () => {
    const { hook, submitApi } = setup();
    act(() => hook.result.current.beginAttempt());
    await act(async () => {
      await hook.result.current.submit(DRAFT);
    });
    act(() => hook.result.current.beginAttempt());
    await act(async () => {
      await hook.result.current.submit(DRAFT);
    });
    const keys = keysSent(submitApi);
    expect(keys[0]).toBe("key-1");
    expect(keys[1]).toBe("key-2");
  });

  it("cancelAttempt discards the in-flight key", async () => {
    const { hook, submitApi } = setup();
    act(() => hook.result.current.beginAttempt());
    // fecha sem enviar → próxima tentativa começa do zero
    act(() => hook.result.current.cancelAttempt());
    act(() => hook.result.current.beginAttempt());
    await act(async () => {
      await hook.result.current.submit(DRAFT);
    });
    expect(keysSent(submitApi)[0]).toBe("key-2");
  });
});
