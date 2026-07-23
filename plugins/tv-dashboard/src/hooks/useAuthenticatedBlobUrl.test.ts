import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as httpClient from "../api/httpClient";
import { useAuthenticatedBlobUrl } from "./useAuthenticatedBlobUrl";

describe("useAuthenticatedBlobUrl", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("marca loading assim que há apiUrl (evita placeholder vazio no 1º frame)", () => {
    vi.spyOn(httpClient, "httpGetBlob").mockImplementation(
      () => new Promise(() => undefined),
    );
    const { result } = renderHook(() =>
      useAuthenticatedBlobUrl("/apps/tv-dashboard-api/playlists/p1/media/a1"),
    );
    expect(result.current.loading).toBe(true);
    expect(result.current.src).toBeUndefined();
    expect(result.current.error).toBe(false);
  });

  it("expõe object URL após o blob carregar", async () => {
    const blob = new Blob(["x"], { type: "image/png" });
    vi.spyOn(httpClient, "httpGetBlob").mockResolvedValue(blob);
    const createSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:test");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);

    const { result } = renderHook(() =>
      useAuthenticatedBlobUrl("/apps/tv-dashboard-api/playlists/p1/media/a1"),
    );

    await waitFor(() => {
      expect(result.current.src).toBe("blob:test");
      expect(result.current.loading).toBe(false);
    });
    expect(createSpy).toHaveBeenCalledWith(blob);
  });

  it("não aplica blob de request cancelado (troca rápida de url)", async () => {
    let resolveFirst: ((blob: Blob) => void) | undefined;
    const first = new Promise<Blob>((resolve) => {
      resolveFirst = resolve;
    });
    const secondBlob = new Blob(["b"], { type: "image/png" });
    const getBlob = vi
      .spyOn(httpClient, "httpGetBlob")
      .mockImplementationOnce(() => first)
      .mockResolvedValueOnce(secondBlob);
    vi.spyOn(URL, "createObjectURL").mockImplementation((value) =>
      value === secondBlob ? "blob:second" : "blob:first",
    );
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);

    const { result, rerender } = renderHook(
      ({ url }: { url: string | undefined }) => useAuthenticatedBlobUrl(url),
      { initialProps: { url: "/media/a" as string | undefined } },
    );

    rerender({ url: "/media/b" });
    await act(async () => {
      resolveFirst?.(new Blob(["a"], { type: "image/png" }));
    });

    await waitFor(() => {
      expect(result.current.src).toBe("blob:second");
    });
    expect(getBlob).toHaveBeenCalledTimes(2);
  });
});
