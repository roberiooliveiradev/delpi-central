import { describe, expect, it } from "vitest";

import { resolveDetailSurfaceState, resolveListSurfaceState } from "./pageState";

describe("pageState", () => {
  it("shows loading on first load", () => {
    expect(
      resolveListSurfaceState({
        loading: true,
        error: null,
        itemCount: 0,
        hasLoaded: false,
      }),
    ).toBe("loading");
  });

  it("shows empty list without treating as error", () => {
    expect(
      resolveListSurfaceState({
        loading: false,
        error: null,
        itemCount: 0,
        hasLoaded: true,
      }),
    ).toBe("empty");
  });

  it("shows api error state", () => {
    expect(
      resolveListSurfaceState({
        loading: false,
        error: "Falha",
        itemCount: 0,
        hasLoaded: true,
      }),
    ).toBe("error");
  });

  it("maps detail 404 to error surface", () => {
    expect(
      resolveDetailSurfaceState({
        open: true,
        loading: false,
        error: "Solicitação não encontrada ou indisponível.",
        notFound: true,
        hasData: false,
      }),
    ).toBe("error");
  });
});
